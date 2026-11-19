"""配当利回り(jvqm_dividend_yield)の単位変換・単位健全性チェックのテスト。

実行: PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_dividend_yield.py

注意: 本体モジュールはimport時に load_dotenv() で .env を読み込む。import前に
Webhook/Supabaseの環境変数を無害なダミー値で埋めて（load_dotenvは既存値を上書きしない）、
さらに requests.post を全テストで差し替えて、実Webhookへ送信されないようにしている。
時刻には依存しない。
"""
import math
import os
import sys
from pathlib import Path

for _k in ("DISCORD_WEBHOOK_URL", "DISCORD_BASIC_WEBHOOK_URL", "DISCORD_PREMIUM_WEBHOOK_URL",
           "DISCORD_ANALYSIS_WEBHOOK_URL", "DISCORD_CHART_WEBHOOK_URL"):
    os.environ[_k] = "http://invalid.example/dummy-webhook"
os.environ["SUPABASE_URL"] = "http://invalid.example"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "dummy"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

import stock_screener_v3_multiplan as m


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """requests.post は記録だけして実送信しない。"""
    calls = []

    def fake_post(url, *a, **kw):
        calls.append((url, kw.get("json")))

        class R:
            status_code = 200
            text = ""
        return R()

    monkeypatch.setattr(m.requests, "post", fake_post)
    return calls


def _data(price=1000.0):
    return pd.DataFrame({"Close": [price] * 30})


def _jvqm(div_yield, **extra):
    info = {"dividendYield": div_yield}
    info.update(extra)
    return m.calc_jvqm(info, _data())


# ── (a)(b)(c) parse_dividend_yield ──────────────────────────────

def test_percent_input_is_kept_as_is():
    assert m.parse_dividend_yield(2.98) == (2.98, "ok")


def test_calc_jvqm_percent_input_not_multiplied():
    r = _jvqm(2.98)
    assert abs(r["jvqm_dividend_yield"] - 2.98) <= 0.05
    assert r["jvqm_dividend_yield"] != 298


@pytest.mark.parametrize("raw,status", [
    (None, "missing"), (0, "missing"), (0.0, "missing"),
    (float("nan"), "invalid"), (float("inf"), "invalid"), (float("-inf"), "invalid"),
    ("abc", "invalid"),
    (-1.0, "out_of_range"), (298.0, "out_of_range"), (30.01, "out_of_range"),
])
def test_abnormal_inputs_become_none(raw, status):
    assert m.parse_dividend_yield(raw) == (None, status)


def test_row_upper_bound_is_inclusive():
    assert m.parse_dividend_yield(30.0) == (30.0, "ok")


def test_decimal_input_is_kept_not_scaled():
    # 小数(0.0298)で来た場合は行単位では範囲内として通る（検知はバッチの中央値側）
    assert m.parse_dividend_yield(0.0298) == (0.03, "ok")


# ── (e) スコア閾値(%単位) ───────────────────────────────────────

def _div_points(div_yield):
    """配当項だけの加点を取り出す（他項目はinfoに無いので0。tseも0）。"""
    return _jvqm(div_yield)["jvqm_score"]


def test_score_thresholds_in_percent():
    assert _div_points(3.5) == 2
    assert _div_points(3.0) == 2
    assert _div_points(2.0) == 1
    assert _div_points(1.5) == 1
    assert _div_points(1.0) == 0
    assert _div_points(0.04) == 0   # 修正前は(×100で4.0)+2だった
    assert _div_points(None) == 0
    assert _div_points(298.0) == 0  # 範囲外はNone化されて加点なし


def test_calc_jvqm_exposes_status():
    assert _jvqm(298.0)["jvqm_dividend_yield"] is None
    assert _jvqm(298.0)["jvqm_dividend_yield_status"] == "out_of_range"
    assert _jvqm(2.0)["jvqm_dividend_yield_status"] == "ok"


# ── 照合 (dividendRate / 株価) ──────────────────────────────────

def test_crosscheck():
    assert m.crosscheck_dividend_yield(30.0, 1000.0, 3.0) == "ok"        # 3.0%
    assert m.crosscheck_dividend_yield(30.0, 1000.0, 300.0) == "mismatch"
    assert m.crosscheck_dividend_yield(None, 1000.0, 3.0) is None
    assert m.crosscheck_dividend_yield(30.0, 0, 3.0) is None
    assert m.crosscheck_dividend_yield(30.0, 1000.0, None) is None
    assert m.crosscheck_dividend_yield(30.0, float("nan"), 3.0) is None


def test_calc_jvqm_crosscheck_uses_last_close():
    r = m.calc_jvqm({"dividendYield": 3.0, "dividendRate": 30.0}, _data(1000.0))
    assert r["jvqm_dividend_crosscheck"] == "ok"
    r = m.calc_jvqm({"dividendYield": 3.0, "dividendRate": 300.0}, _data(1000.0))
    assert r["jvqm_dividend_crosscheck"] == "mismatch"


# ── (c)(d) バッチ単位チェック ───────────────────────────────────

def _rec(raw):
    y, st = m.parse_dividend_yield(raw)
    return {"jvqm_dividend_yield": y, "jvqm_dividend_yield_status": st}


def _batch(raws):
    return [_rec(x) for x in raws]


NORMAL = [None] * 20 + [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 2.2, 2.8, 3.1] * 10


def test_batch_normal_is_ok():
    c = m.check_dividend_yield_sanity(_batch(NORMAL))
    assert c["anomaly"] is False
    assert 0.5 <= c["stats"]["median"] <= 8


def test_batch_100x_values_flagged():
    # 修正前の状態（約100倍）: ほとんどが30超で範囲外
    c = m.check_dividend_yield_sanity(_batch([x * 100 if x else None for x in NORMAL]))
    assert c["anomaly"] is True
    assert c["stats"]["out_of_range"] > 0


def test_batch_decimal_values_flagged_by_median():
    # yfinanceが小数(0.0298)に戻った場合: 行は範囲内だが中央値が下限未満
    c = m.check_dividend_yield_sanity(_batch([x / 100 if x else None for x in NORMAL]))
    assert c["anomaly"] is True
    assert any("中央値" in r for r in c["reasons"])


def test_batch_out_of_range_ratio_over_5pct_flagged():
    raws = NORMAL + [298.0] * 20   # 20/120 > 5%
    assert m.check_dividend_yield_sanity(_batch(raws))["anomaly"] is True


def test_batch_few_outliers_under_5pct_ok():
    raws = NORMAL + [298.0] * 2    # 2/102 < 5%
    assert m.check_dividend_yield_sanity(_batch(raws))["anomaly"] is False


def test_batch_missing_field_flagged_by_coverage():
    c = m.check_dividend_yield_sanity(_batch([None] * 200 + [2.0] * 5))
    assert c["anomaly"] is True
    assert any("消失" in r for r in c["reasons"])


def test_batch_small_sample_skips_median_check():
    # MAX_STOCKSによる少数テスト実行: 中央値は見ない（誤検知防止）
    assert m.check_dividend_yield_sanity(_batch([0.2, 0.3, 0.1]))["anomaly"] is False


def test_batch_ignores_failed_fetch_rows():
    recs = _batch(NORMAL) + [{"fetch_success": False}] * 500
    assert m.check_dividend_yield_sanity(recs)["anomaly"] is False


def test_run_check_notifies_once_on_anomaly_via_mock(_no_network):
    anomaly = m.run_dividend_unit_check(_batch([x * 100 if x else None for x in NORMAL]))
    assert anomaly is True
    assert len(_no_network) == 1                      # 通知関数は1回（requests.postはモック）
    assert "invalid.example" in _no_network[0][0]     # ダミーURLにしか送っていない
    assert "298" not in str(_no_network[0][1])        # 個別の値は通知文に載せない


def test_run_check_silent_on_normal(_no_network):
    assert m.run_dividend_unit_check(_batch(NORMAL)) is False
    assert _no_network == []


def test_json_safe_nan_regression():
    # 既存の関門(_json_safe_float)が変わっていないこと
    assert m._json_safe_float(float("nan")) is None
    assert m._json_safe_float(2.5) == 2.5
    assert not math.isnan(m.parse_dividend_yield(2.5)[0])


def _anomaly_posts(calls):
    return [c for c in calls if "単位チェック" in str(c[1])]


def test_aggregate_anomaly_notifies_and_warns_but_exits_zero(monkeypatch, _no_network, capsys):
    # ユーザー決定(b): 異常時も終了コードは0（SystemExitを出さない）。通知1回＋::warning::行
    bad = _batch([x * 100 if x else None for x in NORMAL])
    monkeypatch.setattr(m, "load_and_merge_shard_results",
                        lambda: ([], 220, {}, bad, 200))
    monkeypatch.setattr(m, "export_snapshot_to_supabase", lambda *a, **k: None)
    m.run_aggregate_screen()   # SystemExitが出ない
    assert len(_anomaly_posts(_no_network)) == 1
    assert "::warning title=" in capsys.readouterr().out


def test_aggregate_normal_no_anomaly_notification(monkeypatch, _no_network, capsys):
    monkeypatch.setattr(m, "load_and_merge_shard_results",
                        lambda: ([], 220, {}, _batch(NORMAL), 200))
    monkeypatch.setattr(m, "export_snapshot_to_supabase", lambda *a, **k: None)
    m.run_aggregate_screen()
    assert _anomaly_posts(_no_network) == []
    assert "::warning" not in capsys.readouterr().out


def test_run_check_prints_warning_annotation(capsys):
    m.run_dividend_unit_check(_batch([x * 100 if x else None for x in NORMAL]))
    out = capsys.readouterr().out
    assert any(line.startswith("::warning title=") for line in out.splitlines())
    assert "298" not in [l for l in out.splitlines() if l.startswith("::warning")][0]
