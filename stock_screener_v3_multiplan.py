#!/usr/bin/env python3
"""
日本市場全銘柄テクニカルスクリーニングシステム v3.0 - Multi-Plan Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【3プラン対応 + 段階的リリース設計】

■ リリースロードマップ
  Phase 1: 暫定無償版（PLAN_MODE=free_beta）
    - 全64件をHTMLレポート化して GitHub Pages で公開
    - Slack/Discordには選抜3件のみ通知（中位×多様性戦略）
    - 認証なし、誰でもアクセス可能

  Phase 2: ベーシック分離（PLAN_MODE=basic）
    - 無償版：中位3件のみ通知、HTMLリンクなし
    - ベーシック：全件HTML（当日分のみ）
    - 簡易認証導入

  Phase 3: プレミアム実装（PLAN_MODE=premium）
    - 30日分アーカイブ + 各銘柄チャート生成
    - Stripe連携・認証強化

■ 技術スタック（yfinanceのみ）
  【価格・出来高データ（history）から計算】
    - ボリンジャーバンド (BB%b / バンド幅)
    - 出来高分析 (前日比・30日平均比)
    - OBV (オン・バランス・ボリューム) + トレンド
    - VWAP近似値 (日足終値ベース)
    - SMA 25 / 75 / 200 + 移動平均乖離率
    - 一目均衡表 (転換線・基準線・先行スパン雲・遅行スパン)
    - MA200上昇トレンド判定
    - 底値200日線クロス / MA50/100 ゴールデンクロス

  【ticker.info（統計データ）から取得】
    - 信用倍率 / Short Ratio / Short % of Float（主に米国株）

  【総合スコアリング】
    - 0〜100点の点数化（配点はSCORE_WEIGHTSで管理）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import json
import os
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from pathlib import Path
import warnings
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # GitHub Actions では不要
warnings.filterwarnings('ignore')
import jpholiday
import sys


# ─────────────────────────────────────────────
#  定数定義
# ─────────────────────────────────────────────
BB_PERIOD        = 20       # ボリンジャーバンド期間
BB_STD           = 2.0      # ボリンジャーバンド 標準偏差倍率
OBV_TREND_DAYS   = 10       # OBV トレンド判定期間
ICHIMOKU_CONV    = 9        # 一目均衡表 転換線期間
ICHIMOKU_BASE    = 26       # 一目均衡表 基準線期間
ICHIMOKU_SPAN2   = 52       # 一目均衡表 先行スパン2期間
ICHIMOKU_LAG     = 26       # 一目均衡表 遅行スパンずれ
MA_SHORT         = 25       # 短期MA（日本株標準）
MA_MID           = 75       # 中期MA（日本株標準）
MA_LONG          = 200      # 長期MA
SCORE_WEIGHTS = {            # 総合スコア配点（合計100点）
    'ma_trend'        : 15,  # MA200上昇（価格>MA200 かつ上昇トレンド）
    'golden_cross'    : 10,  # ゴールデンクロス
    'bottom_cross'    : 10,  # 底値クロス
    'bb_signal'       : 15,  # BB位置 (反発 or ブレイクアウト)
    'obv_trend'       : 10,  # OBV上昇トレンド
    'ichimoku_cloud'  : 10,  # 一目均衡表 雲の上
    'ichimoku_sanryo' : 10,  # 一目均衡表 三役好転（+10追加）
    'volume_surge'    : 10,  # 出来高急増
    'pbr_value'       : 10,  # PBR割安（<1.0）
}


class TechnicalIndicators:
    """
    テクニカル指標計算クラス（yfinanceデータのみで完結）
    各メソッドはpd.DataFrameを受け取り、列を追加して返す。
    """

    # ── ボリンジャーバンド ──────────────────────────────────────────
    @staticmethod
    def bollinger_bands(data: pd.DataFrame,
                        period: int = BB_PERIOD,
                        std_dev: float = BB_STD) -> pd.DataFrame:
        """
        ボリンジャーバンドと %b・バンド幅を計算

        追加列:
          BB_Middle : 中央線 (SMA)
          BB_Upper  : アッパーバンド
          BB_Lower  : ロワーバンド
          BB_Pct_B  : %b = (終値 - Lower) / (Upper - Lower)
                      0以下 = 下限割れ（売られすぎ / 反発候補）
                      1以上 = 上限突破（強いブレイクアウト候補）
          BB_Width  : バンド幅 = (Upper - Lower) / Middle（スクイーズ検知）
        """
        df = data.copy()
        close = df['Close']
        df['BB_Middle'] = close.rolling(period).mean()
        std = close.rolling(period).std()
        df['BB_Upper'] = df['BB_Middle'] + std_dev * std
        df['BB_Lower'] = df['BB_Middle'] - std_dev * std
        band_range = df['BB_Upper'] - df['BB_Lower']
        df['BB_Pct_B'] = (close - df['BB_Lower']) / band_range.replace(0, np.nan)
        df['BB_Width'] = band_range / df['BB_Middle'].replace(0, np.nan)
        return df

    # ── OBV（オン・バランス・ボリューム）──────────────────────────────
    @staticmethod
    def obv(data: pd.DataFrame, trend_days: int = OBV_TREND_DAYS) -> pd.DataFrame:
        """
        OBVとそのトレンド（上昇/下降）を計算

        追加列:
          OBV             :累積OBV値
          OBV_SMA         : OBVの短期移動平均
          OBV_Trend_Up    : bool - OBVが上昇トレンドならTrue
          OBV_Divergence  : bool - 価格が下落しているのにOBVが上昇（強気ダイバージェンス）
        """
        df = data.copy()
        close = df['Close']
        volume = df['Volume']

        direction = np.sign(close.diff().fillna(0))
        obv_series = (direction * volume).cumsum()
        df['OBV'] = obv_series

        df['OBV_SMA'] = obv_series.rolling(trend_days).mean()
        df['OBV_Trend_Up'] = obv_series.iloc[-1] > obv_series.iloc[-trend_days] if len(df) >= trend_days else False

        # 強気ダイバージェンス: 直近trend_days間、価格下落 & OBV上昇
        if len(df) >= trend_days:
            price_down = close.iloc[-1] < close.iloc[-trend_days]
            obv_up = obv_series.iloc[-1] > obv_series.iloc[-trend_days]
            df['OBV_Divergence'] = price_down and obv_up
        else:
            df['OBV_Divergence'] = False

        return df

    # ── 出来高分析 ──────────────────────────────────────────────────
    @staticmethod
    def volume_analysis(data: pd.DataFrame, avg_period: int = 30) -> pd.DataFrame:
        """
        出来高の前日比・平均比を計算

        追加列:
          Volume_Ratio_1d   : 前日比倍率
          Volume_Ratio_Avg  : 30日平均比倍率（1.5以上 = 急増）
          Volume_Yen        : 売買代金（円）
        """
        df = data.copy()
        vol = df['Volume']
        df['Volume_Yen'] = df['Close'] * vol
        df['Volume_Ratio_1d'] = vol / vol.shift(1).replace(0, np.nan)
        df['Volume_MA'] = vol.rolling(avg_period).mean()
        df['Volume_Ratio_Avg'] = vol / df['Volume_MA'].replace(0, np.nan)
        return df

    # ── VWAP（日足終値ベース近似）─────────────────────────────────────
    @staticmethod
    def vwap_daily_approx(data: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        日足データを用いたVWAP近似（(H+L+C)/3 × Volume の累積比）

        ※ 真のVWAPは日中足が必要。これはセッション内近似値。
        追加列:
          VWAP_Approx : 期間内のVWAP近似値
          Above_VWAP  : 現在値がVWAPを上回っているか
        """
        df = data.copy()
        typical = (df['High'] + df['Low'] + df['Close']) / 3
        tp_vol = typical * df['Volume']
        df['VWAP_Approx'] = tp_vol.rolling(period).sum() / df['Volume'].rolling(period).sum()
        df['Above_VWAP'] = df['Close'] > df['VWAP_Approx']
        return df

    # ── 移動平均 & 乖離率 ─────────────────────────────────────────────
    @staticmethod
    def moving_averages(data: pd.DataFrame) -> pd.DataFrame:
        """
        MA25 / MA75 / MA200 と乖離率を計算

        追加列:
          MA25 / MA75 / MA200
          MA25_Dev  : 25日乖離率 (%)   正 = 上方乖離
          MA75_Dev  : 75日乖離率 (%)
        """
        df = data.copy()
        close = df['Close']
        for period, col in [(MA_SHORT, 'MA25'), (MA_MID, 'MA75'), (MA_LONG, 'MA200')]:
            df[col] = close.rolling(period).mean()

        df['MA25_Dev'] = (close - df['MA25']) / df['MA25'].replace(0, np.nan) * 100
        df['MA75_Dev'] = (close - df['MA75']) / df['MA75'].replace(0, np.nan) * 100
        return df

    # ── 一目均衡表 ───────────────────────────────────────────────────
    @staticmethod
    def ichimoku(data: pd.DataFrame) -> pd.DataFrame:
        """
        一目均衡表を計算（転換線・基準線・先行スパン1/2・遅行スパン）

        追加列:
          Ichi_Conv   : 転換線  (9期間高値+安値)/2
          Ichi_Base   : 基準線  (26期間高値+安値)/2
          Ichi_SpanA  : 先行スパン1 (26期間先に描画)
          Ichi_SpanB  : 先行スパン2 (26期間先に描画)
          Ichi_Lag    : 遅行スパン  (26期間前にシフト)
          Ichi_Cloud_Thick : 雲の厚さ（絶対値）
          Ichi_Price_in_Cloud  : 価格が雲の中
          Ichi_Price_above_Cloud : 価格が雲の上
          Ichi_Bullish : bool - 買いゾーン判定
        """
        df = data.copy()
        high = df['High']
        low  = df['Low']
        close = df['Close']

        # 転換線・基準線
        def mid(h, l, p):
            return (h.rolling(p).max() + l.rolling(p).min()) / 2

        df['Ichi_Conv'] = mid(high, low, ICHIMOKU_CONV)
        df['Ichi_Base'] = mid(high, low, ICHIMOKU_BASE)

        # 先行スパン（26日先シフトのため、現在の最新値を計算）
        df['Ichi_SpanA'] = ((df['Ichi_Conv'] + df['Ichi_Base']) / 2).shift(ICHIMOKU_LAG)
        df['Ichi_SpanB'] = mid(high, low, ICHIMOKU_SPAN2).shift(ICHIMOKU_LAG)

        # 遅行スパン（現在の終値を26日前にシフト）
        df['Ichi_Lag'] = close.shift(-ICHIMOKU_LAG)

        # 雲の分析（先行スパンはシフト前の現在値を使う）
        span_a_now = (df['Ichi_Conv'] + df['Ichi_Base']) / 2
        span_b_now = mid(high, low, ICHIMOKU_SPAN2)
        cloud_top    = np.maximum(span_a_now, span_b_now)
        cloud_bottom = np.minimum(span_a_now, span_b_now)

        df['Ichi_Cloud_Thick']       = (cloud_top - cloud_bottom) / close.replace(0, np.nan) * 100
        df['Ichi_Price_above_Cloud'] = close > cloud_top
        df['Ichi_Price_in_Cloud']    = (close >= cloud_bottom) & (close <= cloud_top)

        # 三役好転（簡易版）:
        #   1. 終値 > 雲の上
        #   2. 転換線 > 基準線
        #   3. 遅行スパン > 26日前の終値（= close > close.shift(26)）
        tenkan_above_kijun = df['Ichi_Conv'] > df['Ichi_Base']
        lag_above_price    = close > close.shift(ICHIMOKU_LAG)
        df['Ichi_Bullish'] = (
            df['Ichi_Price_above_Cloud'] &
            tenkan_above_kijun &
            lag_above_price
        )
        return df


class ScoringEngine:
    """
    各指標を 0〜100 点の総合スコアに変換するエンジン
    各シグナルのON/OFFとスコア配点は SCORE_WEIGHTS で管理
    """

    @staticmethod
    def score(row: pd.Series, signals: Dict) -> Tuple[float, Dict]:
        """
        signals: {key: bool} の辞書から総合スコアを計算
        Returns: (total_score, detail_dict)
        """
        detail = {}
        total = 0.0

        for key, weight in SCORE_WEIGHTS.items():
            if signals.get(key, False):
                total += weight
                detail[key] = weight
            else:
                detail[key] = 0

        return round(total, 1), detail


class HTMLReportGenerator:
    """
    HTMLレポート生成クラス（ベーシック・プレミアム対応）
    GitHub Pages用の静的HTMLを生成
    """

    def __init__(self, output_dir: str = "docs"):
        """
        Args:
            output_dir: 出力ディレクトリ（GitHub Pagesのルート）
        """
        self.output_dir = Path(output_dir)
        self.reports_dir = self.output_dir / "reports"
        self.premium_dir = self.output_dir / "premium"
        self.assets_dir = self.output_dir / "assets"

        self.charts_dir = self.output_dir / "charts"
        # ディレクトリ作成
        for d in [self.reports_dir, self.premium_dir, self.assets_dir, self.charts_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    # チャート生成（Premium Step1）
    # ─────────────────────────────────────────────────────────────────────────

    def generate_stock_chart(self, code: str, name: str, date_str: str) -> Optional[str]:
        """
        単一銘柄のローソク足チャートを生成。
        Returns: 相対パス 'charts/YYYYMMDD/CODE.png'、失敗時は None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import mplfinance as mpf

            # Windows 日本語フォント
            plt.rcParams['font.family'] = ['Yu Gothic', 'Meiryo', 'DejaVu Sans']

            ticker_obj = yf.Ticker(f"{code}.T")
            data = ticker_obj.history(period='3mo')

            if data.empty or len(data) < 20:
                return None

            data.index = pd.to_datetime(data.index).tz_localize(None)

            # 移動平均
            data['MA25']  = data['Close'].rolling(25, min_periods=1).mean()
            data['MA75']  = data['Close'].rolling(75, min_periods=1).mean()
            data['MA200'] = data['Close'].rolling(200, min_periods=20).mean()

            # ボリンジャーバンド（20日）
            ma20            = data['Close'].rolling(20, min_periods=1).mean()
            std20           = data['Close'].rolling(20, min_periods=1).std()
            data['BB_upper'] = ma20 + 2 * std20
            data['BB_lower'] = ma20 - 2 * std20

            # スタイル設定（ダーク）
            mc    = mpf.make_marketcolors(
                up='#22c55e', down='#ef4444',
                wick={'up': '#22c55e', 'down': '#ef4444'},
                edge={'up': '#22c55e', 'down': '#ef4444'},
                volume={'up': '#22c55e80', 'down': '#ef444480'},
            )
            style = mpf.make_mpf_style(
                marketcolors=mc,
                facecolor='#1a1a2e',
                figcolor='#0d0d1a',
                gridcolor='#334155',
                gridstyle='-',
                y_on_right=False,
                rc={
                    'axes.labelcolor' : '#94a3b8',
                    'xtick.color'     : '#94a3b8',
                    'ytick.color'     : '#94a3b8',
                    'axes.edgecolor'  : '#334155',
                },
            )

            addplots = [
                mpf.make_addplot(data['MA25'],     color='#60a5fa', width=1.0),
                mpf.make_addplot(data['MA75'],     color='#fbbf24', width=1.0),
                mpf.make_addplot(data['BB_upper'], color='#a78bfa', width=0.8, linestyle='--'),
                mpf.make_addplot(data['BB_lower'], color='#a78bfa', width=0.8, linestyle='--'),
            ]
            if data['MA200'].dropna().shape[0] >= 5:
                addplots.append(mpf.make_addplot(data['MA200'], color='#f87171', width=1.5))

            chart_dir  = self.output_dir / "charts" / date_str
            chart_dir.mkdir(parents=True, exist_ok=True)
            filepath   = chart_dir / f"{code}.png"

            mpf.plot(
                data, type='candle', style=style,
                title=f'{code} {name}',
                volume=True,
                addplot=addplots,
                figsize=(10, 6),
                savefig=dict(fname=str(filepath), dpi=100,
                             bbox_inches='tight', facecolor='#0d0d1a'),
            )
            plt.close('all')
            return f"charts/{date_str}/{code}.png"

        except Exception as e:
            print(f"  ⚠️ チャート生成エラー ({code}): {e}")
            return None

    def _render_stats_section(self, stats_paths: Dict[str, str]) -> str:
        """統計グラフセクションのHTMLを生成"""
        if not stats_paths:
            return ""
        sig_img = stats_paths.get('signals', '')
        sec_img = stats_paths.get('sectors', '')
        if not sig_img and not sec_img:
            return ""

        imgs = ""
        if sig_img:
            imgs += f'<div style="flex:1;min-width:280px;"><img src="../{sig_img}" alt="シグナルヒット率" style="width:100%;border-radius:8px;"></div>'
        if sec_img:
            imgs += f'<div style="flex:1;min-width:280px;"><img src="../{sec_img}" alt="セクター平均スコア" style="width:100%;border-radius:8px;"></div>'

        return f"""
            <div class="section-title">📊 シグナル統計グラフ（Step2）</div>
            <div style="display:flex;flex-wrap:wrap;gap:12px;padding:16px;background:#0f172a;">
                {imgs}
            </div>"""

    def _render_chart_section(self, top5: List[Dict], chart_paths: Dict[str, str],
                               date_str: str) -> str:
        """Top5チャートセクションのHTMLを生成"""
        if not chart_paths:
            return ""

        cards = ""
        for r in top5:
            code = r['code']
            path = chart_paths.get(code)
            if not path:
                continue
            sc = r['total_score']
            sc_color = '#22c55e' if sc >= 70 else '#f59e0b' if sc >= 50 else '#ef4444'
            cards += f"""
            <div style="background:#1e293b;border-radius:10px;overflow:hidden;border:1px solid #334155;">
                <div style="padding:8px 12px;background:#0f172a;display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#f0f0f0;font-weight:bold;font-size:.9em;">{code} {r['name']}</span>
                    <span style="color:{sc_color};font-weight:bold;font-size:.9em;">▶ {sc:.0f}pt</span>
                </div>
                <img src="../{path}" alt="{code}チャート"
                     style="width:100%;display:block;max-height:280px;object-fit:contain;background:#0d0d1a;">
            </div>"""

        return f"""
            <div class="section-title">📈 Top5 スコアチャート（ローソク足 3ヶ月 / MA25・MA75・MA200・BB）</div>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));
                        gap:12px;padding:16px;background:#0f172a;">
                {cards}
            </div>"""

    def generate_stats_charts(self, results: List[Dict], date_str: str) -> Dict[str, str]:
        """
        シグナル統計グラフ（Step2）を生成。
        Returns: {'signals': path, 'sectors': path}
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            plt.rcParams['font.family'] = ['Yu Gothic', 'Meiryo', 'DejaVu Sans']

            chart_dir = self.output_dir / "charts" / date_str
            chart_dir.mkdir(parents=True, exist_ok=True)
            paths: Dict[str, str] = {}
            total = len(results)
            if total == 0:
                return paths

            # ── ① 9指標ヒット率棒グラフ ──────────────────────────────────
            indicator_defs = [
                ('ma_trend',        'MA200上昇',  '#60a5fa'),
                ('golden_cross',    'GC',          '#34d399'),
                ('bottom_cross',    '底値クロス',  '#a78bfa'),
                ('bb_signal',       'BB',          '#f472b6'),
                ('obv_trend',       'OBV',         '#38bdf8'),
                ('ichimoku_cloud',  '雲の上',      '#fb923c'),
                ('ichimoku_sanryo', '三役好転',    '#fbbf24'),
                ('volume_surge',    '出来高急増',  '#4ade80'),
                ('pbr_value',       'PBR割安',     '#c084fc'),
            ]
            labels   = [d[1] for d in indicator_defs]
            hit_rates = []
            for key, _, _ in indicator_defs:
                cnt = sum(1 for r in results if r.get(key) == '✅')
                hit_rates.append(cnt / total * 100)

            fig, ax = plt.subplots(figsize=(9, 5), facecolor='#0d0d1a')
            ax.set_facecolor('#1a1a2e')
            colors = [d[2] for d in indicator_defs]
            bars = ax.barh(labels, hit_rates, color=colors, alpha=0.85, height=0.6)
            for bar, val in zip(bars, hit_rates):
                ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                        f'{val:.1f}%', va='center', ha='left',
                        color='#e2e8f0', fontsize=9)
            ax.set_xlabel('ヒット率 (%)', color='#94a3b8', fontsize=9)
            ax.set_title(f'9指標ヒット率  |  対象 {total} 銘柄', color='#f0f0f0', fontsize=11, pad=10)
            ax.tick_params(colors='#94a3b8', labelsize=9)
            ax.spines[:].set_color('#334155')
            ax.set_xlim(0, max(hit_rates) * 1.2 + 5 if hit_rates else 100)
            ax.grid(axis='x', color='#334155', linestyle='--', alpha=0.5)
            plt.tight_layout()
            sig_path = chart_dir / 'stats_signals.png'
            plt.savefig(sig_path, dpi=100, bbox_inches='tight', facecolor='#0d0d1a')
            plt.close(fig)
            paths['signals'] = f"charts/{date_str}/stats_signals.png"

            # ── ② セクター別平均スコア横棒グラフ（上位15） ───────────────
            from collections import defaultdict
            sec_scores: Dict[str, list] = defaultdict(list)
            for r in results:
                sec = r.get('sector') or 'ETF他'
                if sec in ('-', '—', '－', ''):
                    sec = 'ETF他'
                sec_scores[sec].append(r['total_score'])
            sec_avgs = {s: sum(v)/len(v) for s, v in sec_scores.items() if len(v) >= 2}
            sorted_secs = sorted(sec_avgs.items(), key=lambda x: x[1], reverse=True)[:15]
            sec_labels = [s[0] for s in sorted_secs]
            sec_vals   = [s[1] for s in sorted_secs]
            norm_vals  = [(v - min(sec_vals)) / (max(sec_vals) - min(sec_vals) + 0.1)
                          for v in sec_vals]
            bar_colors = [plt.cm.RdYlGn(0.2 + n * 0.6) for n in norm_vals]  # type: ignore

            fig2, ax2 = plt.subplots(figsize=(9, max(4, len(sec_labels) * 0.45)), facecolor='#0d0d1a')
            ax2.set_facecolor('#1a1a2e')
            bars2 = ax2.barh(sec_labels, sec_vals, color=bar_colors, alpha=0.85, height=0.6)
            for bar, val in zip(bars2, sec_vals):
                ax2.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                         f'{val:.1f}', va='center', ha='left',
                         color='#e2e8f0', fontsize=8)
            ax2.set_xlabel('平均スコア (pt)', color='#94a3b8', fontsize=9)
            ax2.set_title('セクター別 平均スコア TOP15', color='#f0f0f0', fontsize=11, pad=10)
            ax2.tick_params(colors='#94a3b8', labelsize=8)
            ax2.spines[:].set_color('#334155')
            ax2.grid(axis='x', color='#334155', linestyle='--', alpha=0.5)
            plt.tight_layout()
            sec_path = chart_dir / 'stats_sectors.png'
            plt.savefig(sec_path, dpi=100, bbox_inches='tight', facecolor='#0d0d1a')
            plt.close(fig2)
            paths['sectors'] = f"charts/{date_str}/stats_sectors.png"

            print(f"  ✅ 統計グラフ生成完了（シグナル + セクター）")
            return paths

        except Exception as e:
            print(f"  ⚠️ 統計グラフ生成エラー: {e}")
            return {}

    def generate_charts_for_top5(self, results: List[Dict], date_str: str) -> Dict[str, str]:
        """
        スコア上位5銘柄のチャートを生成。
        Returns: {code: relative_path}
        """
        top5       = results[:5]
        chart_paths: Dict[str, str] = {}
        print(f"\n📈 Top5チャート生成中...")
        for r in top5:
            code, name = r['code'], r['name']
            print(f"  {code} {name}...", end='', flush=True)
            path = self.generate_stock_chart(code, name, date_str)
            if path:
                chart_paths[code] = path
                print(" ✅")
            else:
                print(" ⚠️ スキップ")
        return chart_paths

    def generate_basic_report(self, results: List[Dict], date: str,
                               sector_report: str = "") -> str:
        """
        ベーシック版HTMLレポートを生成（当日全銘柄）

        Args:
            results: スクリーニング結果
            date: 日付文字列（YYYY-MM-DD）
            sector_report: セクター統計

        Returns:
            生成したHTMLファイルのパス（相対）
        """
        if not results:
            return ""

        date_str = date.replace("-", "")
        filename = f"{date_str}.html"
        filepath = self.reports_dir / filename

        # ソート可能なテーブルHTML
        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>スクリーニング結果 - {date}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 10px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: visible;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 1.1em; }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        .stat-box {{
            text-align: center;
            padding: 15px;
        }}
        .stat-box .number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-box .label {{
            color: #6c757d;
            margin-top: 8px;
            font-size: 0.9em;
        }}
        
        .controls {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        .controls input {{
            padding: 12px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            width: 100%;
            max-width: 400px;
            font-size: 1em;
        }}
        
        /* テーブル - モバイル最適化 */
        .table-container {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            width: 100%;
            max-width: 100%;
            display: block;
            background: white;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 800px;
            background: white;
        }}
        thead {{
            background: #495057;
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        th {{
            padding: 15px 10px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            font-size: 0.95em;
        }}
        th:hover {{ background: #343a40; }}
        th:after {{
            content: ' ↕';
            opacity: 0.5;
            font-size: 0.8em;
        }}
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #e9ecef;
            font-size: 0.9em;
            background: white;
        }}
        tr:hover td {{ background: #f8f9fa; }}
        @media(max-width:600px) {{ th, td {{ padding: 8px 6px; font-size: 0.82em; }} }}
        
        .score-high {{ color: #28a745; font-weight: bold; }}
        .score-mid {{ color: #ffc107; font-weight: bold; }}
        .score-low {{ color: #dc3545; font-weight: bold; }}
        
        .tag {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 600;
            white-space: nowrap;
        }}
        .tag-safe {{ background: #d4edda; color: #155724; }}
        .tag-normal {{ background: #fff3cd; color: #856404; }}
        .tag-risky {{ background: #f8d7da; color: #721c24; }}
        
        .footer {{
            padding: 30px 20px;
            text-align: center;
            background: #f8f9fa;
            color: #6c757d;
            border-top: 2px solid #e9ecef;
        }}
        .footer a {{
            color: #667eea;
            text-decoration: none;
            margin: 0 15px;
            font-weight: 500;
        }}
        .footer a:hover {{ text-decoration: underline; }}
        
        /* スマホ対応（768px以下） */
        @media (max-width: 768px) {{
            body {{ padding: 5px; }}
            .container {{ border-radius: 8px; }}
            
            .header {{ padding: 20px 15px; }}
            .header h1 {{ font-size: 1.4em; }}
            .header p {{ font-size: 0.95em; }}
            
            .stats {{
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                padding: 15px 10px;
            }}
            .stat-box {{ padding: 10px 5px; }}
            .stat-box .number {{ font-size: 1.5em; }}
            .stat-box .label {{ font-size: 0.8em; }}
            
            .controls {{ padding: 15px 10px; }}
            .controls input {{ 
                font-size: 16px; /* iOS zoom防止 */
                max-width: 100%;
            }}
            
            .table-container {{ padding: 0 5px; }}
            th {{ padding: 12px 6px; font-size: 0.85em; }}
            td {{ padding: 10px 6px; font-size: 0.85em; }}
            
            .footer {{ padding: 20px 15px; }}
            .footer a {{ 
                display: block; 
                margin: 10px 0;
            }}
        }}
        
        /* 極小スマホ対応（480px以下） */
        @media (max-width: 480px) {{
            .header h1 {{ font-size: 1.2em; }}
            .header p {{ font-size: 0.85em; }}
            
            .stats {{ grid-template-columns: repeat(3, 1fr); gap: 8px; }}
            .stat-box .number {{ font-size: 1.3em; }}
            .stat-box .label {{ font-size: 0.75em; }}
            
            th {{ padding: 10px 4px; font-size: 0.75em; }}
            td {{ padding: 8px 4px; font-size: 0.75em; }}
            table {{ min-width: 800px; }}
            
            .tag {{ font-size: 0.7em; padding: 3px 6px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 日本株スクリーニング結果</h1>
            <p>📅 {date} | ベーシックプラン</p>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="number">{len(results)}</div>
                <div class="label">該当銘柄数</div>
            </div>
            <div class="stat-box">
                <div class="number">{results[0]['total_score']:.0f}</div>
                <div class="label">最高スコア</div>
            </div>
            <div class="stat-box">
                <div class="number">{len(set(r['sector'] for r in results))}</div>
                <div class="label">セクター数</div>
            </div>
        </div>

        <div class="controls">
            <input type="text" id="search" placeholder="🔍 銘柄名・コードで検索..." onkeyup="filterTable()">
        </div>

        <div class="table-container">
        <table id="stockTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">順位</th>
                    <th onclick="sortTable(1)">コード</th>
                    <th onclick="sortTable(2)">銘柄名</th>
                    <th onclick="sortTable(3)">セクター</th>
                    <th onclick="sortTable(4)">スコア ⭐</th>
                    <th onclick="sortTable(5)">株価</th>
                    <th>シグナル</th>
                    <th>リスク</th>
                </tr>
            </thead>
            <tbody>
"""

        for i, r in enumerate(results, 1):
            score_class = ("score-high" if r['total_score'] >= 70
                          else "score-mid" if r['total_score'] >= 50
                          else "score-low")

            risk_class = ("tag-safe" if "安定" in r['risk_tag']
                         else "tag-normal" if "標準" in r['risk_tag']
                         else "tag-risky")

            signals = []
            if r['bottom_cross'] == '●': signals.append('底値クロス')
            if r['golden_cross'] == '●': signals.append('GC')
            if r['bb_reversal'] == '●': signals.append('BB反発')
            if r['bb_breakout'] == '●': signals.append('BBブレイク')
            if r['volume_surge'] == '●': signals.append('出来高急増')
            if r['obv_trend_up'] == '●': signals.append('OBV↑')
            if r['ichimoku_bullish'] != '－': signals.append('一目好転')

            signal_str = ", ".join(signals) if signals else "－"

            html += f"""
                <tr>
                    <td>{i}</td>
                    <td><strong>{r['code']}</strong></td>
                    <td>{r['name']}</td>
                    <td><small>{r['sector']}</small></td>
                    <td class="{score_class}">{r['total_score']:.0f}</td>
                    <td>¥{r['price']:,.0f}</td>
                    <td><small>{signal_str}</small></td>
                    <td><span class="tag {risk_class}">{r['risk_tag']}</span></td>
                </tr>
"""

        html += """
            </tbody>
        </table>
        </div>

        <div class="footer">
            <p>⚠️ このレポートは当日限り有効です。翌日以降は最新版をご確認ください。</p>
            <p style="margin-top: 15px;">
                <a href="../index.html">🏠 トップページへ</a> |
                <a href="../legal/disclaimer.html">⚠️ 免責事項</a>
            </p>
            <p style="margin-top: 10px; font-size: 0.85em; color: #999;">
                本サービスは投資助言ではありません。投資判断は自己責任で行ってください。
            </p>
        </div>
    </div>

    <script>
        function sortTable(col) {
            const table = document.getElementById("stockTable");
            const rows = Array.from(table.rows).slice(1);
            const isAsc = table.dataset.sortCol == col && table.dataset.sortDir == "asc";

            rows.sort((a, b) => {
                let aVal = a.cells[col].textContent.trim();
                let bVal = b.cells[col].textContent.trim();

                // 数値列の判定
                if (col === 0 || col === 4 || col === 5) {
                    aVal = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                    bVal = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
                }

                return isAsc ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1);
            });

            rows.forEach(row => table.tBodies[0].appendChild(row));
            table.dataset.sortCol = col;
            table.dataset.sortDir = isAsc ? "desc" : "asc";
        }

        function filterTable() {
            const input = document.getElementById("search").value.toUpperCase();
            const table = document.getElementById("stockTable");
            const rows = table.getElementsByTagName("tr");

            for (let i = 1; i < rows.length; i++) {
                const code = rows[i].cells[1].textContent;
                const name = rows[i].cells[2].textContent;
                rows[i].style.display = (code + name).toUpperCase().includes(input) ? "" : "none";
            }
        }
    </script>
<button onclick="window.scrollTo({top:0,behavior:'smooth'})"
        style="position:fixed;bottom:24px;right:24px;z-index:9999;background:#667eea;color:white;border:none;border-radius:50%;width:48px;height:48px;font-size:1.4em;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;line-height:1;"
        title="トップへ戻る">↑</button>
</body>
</html>
"""

        filepath.write_text(html, encoding='utf-8')
        print(f"✅ HTMLレポート生成: {filepath}")
        return f"reports/{filename}"

    def generate_analysis_report(self, results: List[Dict], date: str) -> str:
        """
        #analysis 用HTMLレポート（8指標スコア内訳一覧）
        ETFを除外して生成
        """
        if not results:
            return ""

        # ETF除外
        def _is_etf(r):
            try:
                return 1300 <= int(r.get('code', '0')) <= 1699
            except (ValueError, TypeError):
                return False
        filtered = [r for r in results if not _is_etf(r)]
        if not filtered:
            return ""

        date_str = date.replace("-", "")
        filename = f"{date_str}.html"
        analysis_dir = self.output_dir / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        filepath = analysis_dir / filename

        INDICATORS = [
            ('ma_trend',        'MA200',    15),
            ('golden_cross',    'GC',       10),
            ('bottom_cross',    '底値',     10),
            ('bb_signal',       'BB',       15),
            ('obv_trend',       'OBV',      10),
            ('ichimoku_cloud',  '雲の上',   10),
            ('ichimoku_sanryo', '三役好転', 10),
            ('volume_surge',    '出来高',   10),
            ('pbr_value',       'PBR割安',  10),
        ]

        header_cells = "".join(
            f'<th onclick="sortTable({i+5})">{label}<br><small style="opacity:.7">{pts}点</small></th>'
            for i, (_, label, pts) in enumerate(INDICATORS)
        )

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>スコア内訳レポート - {date}</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',sans-serif; background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%); padding:10px; color:#333; }}
        .container {{ max-width:1600px; margin:0 auto; background:white; border-radius:12px; box-shadow:0 10px 40px rgba(0,0,0,.3); overflow:visible; }}
        .header {{ background:linear-gradient(135deg,#0f3460 0%,#533483 100%); color:white; padding:30px 20px; text-align:center; }}
        .header h1 {{ font-size:1.8em; margin-bottom:8px; }}
        .header p {{ opacity:.9; }}
        .badge {{ display:inline-block; background:rgba(255,255,255,.2); padding:4px 12px; border-radius:20px; font-size:.85em; margin-top:8px; }}
        .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:15px; padding:20px; background:#f8f9fa; border-bottom:2px solid #e9ecef; }}
        .stat-box {{ text-align:center; padding:12px; }}
        .stat-box .number {{ font-size:1.8em; font-weight:bold; color:#533483; }}
        .stat-box .label {{ color:#6c757d; margin-top:6px; font-size:.85em; }}
        .controls {{ padding:15px 20px; background:#f8f9fa; border-bottom:1px solid #dee2e6; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }}
        .controls input {{ padding:10px 14px; border:1px solid #ced4da; border-radius:6px; width:300px; font-size:.95em; }}
        .table-container {{ overflow-x:auto; width:100%; background:white; }}
        table {{ width:100%; border-collapse:collapse; min-width:1100px; background:white; }}
        thead {{ background:#0f3460; color:white; position:sticky; top:0; z-index:10; }}
        th {{ padding:12px 8px; text-align:center; font-weight:600; cursor:pointer; font-size:.85em; user-select:none; }}
        th:hover {{ background:#1a4a80; }}
        th:after {{ content:' ↕'; opacity:.5; font-size:.75em; }}
        td {{ padding:10px 8px; border-bottom:1px solid #e9ecef; font-size:.88em; text-align:center; background:white; }}
        td:nth-child(3) {{ text-align:left; }}
        tr:hover td {{ background:#f0f4ff; }}
        @media(max-width:600px) {{ th, td {{ padding:7px 4px; font-size:.80em; }} }}
        .score-high {{ color:#28a745; font-weight:bold; font-size:1.05em; }}
        .score-mid  {{ color:#ffc107; font-weight:bold; }}
        .score-low  {{ color:#dc3545; font-weight:bold; }}
        .hit  {{ background:#d4edda; color:#155724; border-radius:4px; padding:2px 6px; font-weight:600; }}
        .miss {{ color:#adb5bd; }}
        .footer {{ padding:25px 20px; text-align:center; background:#f8f9fa; color:#6c757d; border-top:2px solid #e9ecef; }}
        .footer a {{ color:#533483; text-decoration:none; margin:0 12px; font-weight:500; }}
        @media(max-width:768px) {{ .controls input {{ width:100%; }} }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🔬 スコア内訳レポート</h1>
        <p>📅 {date} | 全指標スコア内訳（8指標）</p>
        <span class="badge">Basic / Premium プラン</span>
    </div>
    <div class="stats">
        <div class="stat-box"><div class="number">{len(filtered)}</div><div class="label">対象銘柄数</div></div>
        <div class="stat-box"><div class="number">{filtered[0]['total_score']:.0f}</div><div class="label">最高スコア</div></div>
        <div class="stat-box"><div class="number">{sum(r['total_score'] for r in filtered)/len(filtered):.0f}</div><div class="label">平均スコア</div></div>
        <div class="stat-box"><div class="number">{len(set(r['sector'] for r in filtered))}</div><div class="label">セクター数</div></div>
    </div>
    <div class="controls">
        <input type="text" id="search" placeholder="🔍 銘柄名・コードで検索..." onkeyup="filterTable()">
    </div>
    <div class="table-container">
    <table id="stockTable">
        <thead>
            <tr>
                <th onclick="sortTable(0)">順位</th>
                <th onclick="sortTable(1)">コード</th>
                <th onclick="sortTable(2)">銘柄名</th>
                <th onclick="sortTable(3)">セクター</th>
                <th onclick="sortTable(4)">合計</th>
                {header_cells}
            </tr>
        </thead>
        <tbody>
"""
        for i, r in enumerate(filtered, 1):
            sd = r.get('score_detail', {})
            score_cls = ("score-high" if r['total_score'] >= 70
                         else "score-mid" if r['total_score'] >= 50
                         else "score-low")
            indicator_cells = "".join(
                f'<td><span class="{"hit" if sd.get(key,0)>0 else "miss"}">'
                f'{"✅ "+str(int(sd.get(key,0)))+"pt" if sd.get(key,0)>0 else "—"}</span></td>'
                for key, _, _ in INDICATORS
            )
            html += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{r['code']}</strong></td>
                <td style="text-align:left">{r['name']}</td>
                <td><small>{r['sector']}</small></td>
                <td class="{score_cls}">{r['total_score']:.0f}</td>
                {indicator_cells}
            </tr>"""

        html += """
        </tbody>
    </table>
    </div>
    <div class="footer">
        <p>⚠️ このレポートは投資助言ではありません。投資判断は自己責任で行ってください。</p>
        <p style="margin-top:12px;">
            <a href="../index.html">🏠 トップ</a> |
            <a href="../legal/disclaimer.html">⚠️ 免責事項</a>
        </p>
    </div>
</div>
<script>
    function sortTable(col) {
        const table = document.getElementById("stockTable");
        const rows = Array.from(table.rows).slice(1);
        const isAsc = table.dataset.sortCol == col && table.dataset.sortDir == "asc";
        rows.sort((a, b) => {
            let aVal = a.cells[col].textContent.trim().replace(/[^0-9.-]/g,'');
            let bVal = b.cells[col].textContent.trim().replace(/[^0-9.-]/g,'');
            aVal = parseFloat(aVal) || aVal;
            bVal = parseFloat(bVal) || bVal;
            return isAsc ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1);
        });
        rows.forEach(row => table.tBodies[0].appendChild(row));
        table.dataset.sortCol = col;
        table.dataset.sortDir = isAsc ? "desc" : "asc";
    }
    function filterTable() {
        const input = document.getElementById("search").value.toUpperCase();
        const rows = document.getElementById("stockTable").getElementsByTagName("tr");
        for (let i = 1; i < rows.length; i++) {
            const code = rows[i].cells[1].textContent;
            const name = rows[i].cells[2].textContent;
            rows[i].style.display = (code + name).toUpperCase().includes(input) ? "" : "none";
        }
    }
</script>
<button onclick="window.scrollTo({top:0,behavior:'smooth'})"
        style="position:fixed;bottom:24px;right:24px;z-index:9999;background:#667eea;color:white;border:none;border-radius:50%;width:48px;height:48px;font-size:1.4em;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;line-height:1;"
        title="トップへ戻る">↑</button>
</body>
</html>"""

        filepath.write_text(html, encoding='utf-8')
        print(f"✅ Analysisレポート生成: {filepath}")
        return f"analysis/{filename}"

    def generate_premium_report(self, results: List[Dict], date: str,
                                 sector_report: str = "",
                                 chart_paths: Dict[str, str] = None,
                                 stats_paths: Dict[str, str] = None) -> str:
        """
        Premium用HTMLレポート
        - Top5チャート（ローソク足 + MA + BB）
        - BackLog一覧（win_rate降順）
        - セクター別集計・シグナル分布
        - 過去ログへのアーカイブリンク
        """
        if not results:
            return ""

        date_str = date.replace("-", "")
        filename = f"{date_str}.html"
        premium_dir = self.output_dir / "premium"
        premium_dir.mkdir(parents=True, exist_ok=True)
        filepath = premium_dir / filename

        # BackLog順（win_rate降順）
        backlog_sorted = sorted(results, key=lambda x: x.get('win_rate', 0), reverse=True)

        # セクター集計（空・記号セクターを「ETF他」に統一）
        from collections import Counter
        _BLANK = {'', '-', '－', '—', '―', 'N/A', 'n/a', 'nan', 'None'}
        def _normalize_sec(r):
            raw = str(r.get('sector', '') or '').strip()
            return 'ETF他' if raw in _BLANK else raw
        sector_counts = Counter(_normalize_sec(r) for r in results)
        top_sectors = sector_counts.most_common(8)

        # シグナル集計
        signal_defs = [
            ('golden_cross', 'ゴールデンクロス'),
            ('bb_reversal',  'BB反発'),
            ('bb_breakout',  'BBブレイク'),
            ('volume_surge', '出来高急増'),
            ('obv_trend_up', 'OBV上昇'),
        ]
        signal_rows = ""
        for key, label in signal_defs:
            cnt = sum(1 for r in results if r.get(key) == '✅')
            pct = cnt / len(results) * 100 if results else 0
            bar = "█" * min(int(pct / 5), 20)
            signal_rows += f"<tr><td>{label}</td><td>{cnt}銘柄</td><td>{pct:.0f}%</td><td style='color:#f59e0b;letter-spacing:-2px'>{bar}</td></tr>"

        # 過去ログ一覧（Premium / Basic / Analysis 3種）
        reports_dir  = self.output_dir / "reports"
        analysis_dir = self.output_dir / "analysis"

        def _build_archive(directory, rel_prefix, current_stem):
            items = ""
            if directory.exists():
                for af in sorted(directory.glob("*.html"), reverse=True)[:30]:
                    if len(af.stem) == 8:
                        lbl = f"{af.stem[:4]}-{af.stem[4:6]}-{af.stem[6:]}"
                        bold = "font-weight:bold;color:#f59e0b;" if af.stem == current_stem else ""
                        items += f'<li><a href="{rel_prefix}{af.name}" style="{bold}">{lbl}</a></li>'
            return items or '<li style="color:#adb5bd">まだありません</li>'

        archive_premium  = _build_archive(premium_dir,  "",          date_str)
        archive_basic    = _build_archive(reports_dir,  "../reports/",  date_str)
        archive_analysis = _build_archive(analysis_dir, "../analysis/", date_str)

        INDICATORS = [
            ('ma_trend','MA200',15),('golden_cross','GC',10),('bottom_cross','底値',10),
            ('bb_signal','BB',15),('obv_trend','OBV',10),
            ('ichimoku_cloud','雲上',10),('ichimoku_sanryo','三役好転',10),
            ('volume_surge','出来高',10),('pbr_value','PBR',10),
        ]
        indicator_headers = "".join(
            f'<th onclick="sortTable({i+6})">{lbl}<br><small>{pts}pt</small></th>'
            for i,(key,lbl,pts) in enumerate(INDICATORS)
        )

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>プレミアムレポート - {date}</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',sans-serif; background:linear-gradient(135deg,#1a1a2e 0%,#0d0d1a 100%); padding:10px; color:#333; }}
        .container {{ max-width:1700px; margin:0 auto; background:white; border-radius:12px; box-shadow:0 10px 40px rgba(0,0,0,.4); }}
        .header {{ background:linear-gradient(135deg,#7c3aed 0%,#db2777 100%); color:white; padding:30px 20px; text-align:center; }}
        .header h1 {{ font-size:1.9em; margin-bottom:8px; }}
        .badge {{ display:inline-block; background:rgba(255,255,255,.25); padding:4px 14px; border-radius:20px; font-size:.85em; margin-top:8px; }}
        .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:15px; padding:20px; background:#faf5ff; border-bottom:2px solid #e9d5ff; }}
        .stat-box {{ text-align:center; padding:12px; }}
        .stat-box .number {{ font-size:1.8em; font-weight:bold; color:#7c3aed; }}
        .stat-box .label {{ color:#6c757d; margin-top:6px; font-size:.85em; }}
        .layout {{ display:grid; grid-template-columns:1fr 280px; gap:0; }}
        .main-content {{ padding:0; }}
        .sidebar {{ background:#faf5ff; border-left:2px solid #e9d5ff; padding:20px; }}
        .sidebar h3 {{ color:#7c3aed; margin-bottom:8px; font-size:.95em; }}
        .tab-nav {{ display:flex; gap:4px; margin-bottom:12px; flex-wrap:wrap; }}
        .tab-btn {{ padding:5px 10px; border:1px solid #c4b5fd; border-radius:6px; font-size:.8em; cursor:pointer; background:white; color:#7c3aed; }}
        .tab-btn.active {{ background:#7c3aed; color:white; border-color:#7c3aed; }}
        .tab-panel {{ display:none; }}
        .tab-panel.active {{ display:block; }}
        .sidebar ul {{ list-style:none; }}
        .sidebar ul li {{ margin:5px 0; }}
        .sidebar ul li a {{ color:#7c3aed; text-decoration:none; font-size:.88em; }}
        .sidebar ul li a:hover {{ text-decoration:underline; }}
        .coming-soon {{ color:#adb5bd; font-size:.85em; padding:8px; border:1px dashed #e9d5ff; border-radius:6px; text-align:center; margin-top:8px; }}
        .section-title {{ background:#7c3aed; color:white; padding:10px 20px; font-weight:bold; font-size:.95em; }}
        .summary-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:0; }}
        .summary-box {{ padding:20px; border-right:1px solid #e9ecef; border-bottom:1px solid #e9ecef; }}
        .summary-box h4 {{ color:#7c3aed; margin-bottom:12px; font-size:.9em; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }}
        .summary-box table {{ width:100%; font-size:.85em; }}
        .summary-box td {{ padding:5px 8px; border-bottom:1px solid #f0e6ff; }}
        .controls {{ padding:15px 20px; background:#f8f9fa; border-bottom:1px solid #dee2e6; }}
        .controls input {{ padding:10px 14px; border:1px solid #ced4da; border-radius:6px; width:300px; font-size:.9em; }}
        .table-container {{ overflow-x:auto; background:white; }}
        table.main {{ width:100%; border-collapse:collapse; min-width:1300px; background:white; }}
        table.main thead {{ background:#7c3aed; color:white; position:sticky; top:0; z-index:10; }}
        table.main th {{ padding:11px 7px; text-align:center; cursor:pointer; font-size:.82em; font-weight:600; user-select:none; }}
        table.main th:hover {{ background:#6d28d9; }}
        table.main th:after {{ content:' ↕'; opacity:.5; font-size:.7em; }}
        table.main td {{ padding:9px 7px; border-bottom:1px solid #f0e6ff; font-size:.85em; text-align:center; background:white; }}
        table.main td:nth-child(3) {{ text-align:left; }}
        table.main tr:hover td {{ background:#faf5ff; }}
        @media(max-width:600px) {{
            table.main {{ font-size:.78em; }}
            table.main th, table.main td {{ padding:7px 4px; }}
        }}
        .score-high {{ color:#28a745; font-weight:bold; }}
        .score-mid  {{ color:#d97706; font-weight:bold; }}
        .score-low  {{ color:#dc3545; font-weight:bold; }}
        .backlog-high {{ background:#fef3c7; color:#92400e; border-radius:4px; padding:2px 6px; font-weight:bold; }}
        .backlog-mid  {{ background:#ede9fe; color:#5b21b6; border-radius:4px; padding:2px 6px; }}
        .backlog-low  {{ color:#adb5bd; }}
        .hit  {{ background:#d4edda; color:#155724; border-radius:3px; padding:1px 5px; font-weight:600; font-size:.82em; }}
        .miss {{ color:#ced4da; font-size:.82em; }}
        .footer {{ padding:25px 20px; text-align:center; background:#f8f9fa; color:#6c757d; border-top:2px solid #e9ecef; }}
        .footer a {{ color:#7c3aed; text-decoration:none; margin:0 12px; font-weight:500; }}
        @media(max-width:900px) {{ .layout {{ grid-template-columns:1fr; }} .sidebar {{ border-left:none; border-top:2px solid #e9d5ff; }} .summary-grid {{ grid-template-columns:1fr; }} }}
        #nav-panel a {{ color: #93c5fd; text-decoration: none; font-size: 0.85em; display: block; padding: 2px 0; }}
        #nav-panel a:hover {{ color: #f59e0b; }}
        details > ul li a {{ color: #93c5fd; text-decoration: none; font-size: 0.85em; display: block; padding: 2px 0; }}
        details > ul li a:hover {{ color: #f59e0b; }}
        details summary::-webkit-details-marker {{ display: none; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>👑 プレミアムレポート</h1>
        <p>📅 {date}  |  BackLog分析付き</p>
        <span class="badge">Premium プラン限定</span>
    </div>
        <!-- ナビゲーションパネル -->
        <div id="nav-panel" style="background:#1e293b;padding:16px 20px;border-bottom:2px solid #334155;">
            <div style="max-width:1400px;margin:0 auto;display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start;">
                <!-- Premium -->
                <div style="flex:1;min-width:200px;">
                    <div style="color:#f59e0b;font-weight:bold;margin-bottom:8px;font-size:0.95em;">📊 Premiumレポート</div>
                    <div style="color:#f0f0f0;font-size:0.9em;margin-bottom:6px;">📅 {date}（現在）</div>
                    <details style="cursor:pointer;">
                        <summary style="color:#94a3b8;font-size:0.85em;list-style:none;cursor:pointer;">📁 過去レポート ▼</summary>
                        <ul style="list-style:none;margin-top:8px;padding-left:12px;max-height:200px;overflow-y:auto;">
                            {archive_premium}
                        </ul>
                    </details>
                </div>
                <!-- Analysis -->
                <div style="flex:1;min-width:200px;">
                    <div style="color:#60a5fa;font-weight:bold;margin-bottom:8px;font-size:0.95em;">📈 Analysisレポート</div>
                    <div style="font-size:0.9em;margin-bottom:6px;">
                        {f'<a href="../analysis/{date_str}.html" style="color:#93c5fd;">📅 {date}（当日）</a>' if (analysis_dir / filename).exists() else f'<span style="color:#64748b;">📅 {date}（未生成）</span>'}
                    </div>
                    <details style="cursor:pointer;">
                        <summary style="color:#94a3b8;font-size:0.85em;list-style:none;cursor:pointer;">📁 過去レポート ▼</summary>
                        <ul style="list-style:none;margin-top:8px;padding-left:12px;max-height:200px;overflow-y:auto;">
                            {archive_analysis}
                        </ul>
                    </details>
                </div>
                <!-- Basic -->
                <div style="flex:1;min-width:200px;">
                    <div style="color:#34d399;font-weight:bold;margin-bottom:8px;font-size:0.95em;">📋 Basicレポート</div>
                    <div style="font-size:0.9em;margin-bottom:6px;">
                        <a href="../reports/{date_str}.html" style="color:#6ee7b7;">📅 {date}（当日）</a>
                    </div>
                    <details style="cursor:pointer;">
                        <summary style="color:#94a3b8;font-size:0.85em;list-style:none;cursor:pointer;">📁 過去レポート ▼</summary>
                        <ul style="list-style:none;margin-top:8px;padding-left:12px;max-height:200px;overflow-y:auto;">
                            {archive_basic}
                        </ul>
                    </details>
                </div>
            </div>
        </div>
    <div class="stats">
        <div class="stat-box"><div class="number">{len(results)}</div><div class="label">対象銘柄数</div></div>
        <div class="stat-box"><div class="number">{results[0]['total_score']:.0f}</div><div class="label">最高スコア</div></div>
        <div class="stat-box"><div class="number">{backlog_sorted[0]['win_rate']:.0f}%</div><div class="label">BackLog最高値</div></div>
        <div class="stat-box"><div class="number">{sum(r['win_rate'] for r in results)/len(results):.0f}%</div><div class="label">BackLog平均</div></div>
        <div class="stat-box"><div class="number">{len(set(r['sector'] for r in results))}</div><div class="label">セクター数</div></div>
    </div>

    <div class="layout">
        <div class="main-content">
            <div class="summary-grid">
                <div class="summary-box">
                    <h4>📊 セクター別集計</h4>
                    <table>
                        <tr><th style="text-align:left">セクター</th><th>銘柄数</th></tr>
                        {"".join(f'<tr><td>{sec}</td><td style="text-align:center"><strong>{cnt}</strong></td></tr>' for sec,cnt in top_sectors)}
                    </table>
                </div>
                <div class="summary-box">
                    <h4>🔔 シグナル分布</h4>
                    <table>
                        <tr><th style="text-align:left">シグナル</th><th>銘柄数</th><th>%</th><th>分布</th></tr>
                        {signal_rows}
                    </table>
                </div>
            </div>
            {self._render_stats_section(stats_paths or {})}

            {self._render_chart_section(results[:5], chart_paths or {}, date_str)}
            <div class="section-title">🗂️ BackLog一覧（バックテスト参考値 降順）</div>
            <div class="controls">
                <input type="text" id="search" placeholder="🔍 銘柄名・コードで検索..." onkeyup="filterTable()">
            </div>
            <div class="table-container">
            <table class="main" id="stockTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">順位</th>
                        <th onclick="sortTable(1)">コード</th>
                        <th onclick="sortTable(2)">銘柄名</th>
                        <th onclick="sortTable(3)">セクター</th>
                        <th onclick="sortTable(4)">スコア</th>
                        <th onclick="sortTable(5)">BackLog</th>
                        {indicator_headers}
                    </tr>
                </thead>
                <tbody>
"""
        for i, r in enumerate(backlog_sorted, 1):
            sd = r.get('score_detail', {})
            sc = r['total_score']
            wr = r.get('win_rate', 0)
            score_cls = "score-high" if sc >= 70 else "score-mid" if sc >= 50 else "score-low"
            bt_cls = "backlog-high" if wr >= 60 else "backlog-mid" if wr >= 40 else "backlog-low"
            indicator_cells = "".join(
                f'<td><span class="{"hit" if sd.get(k,0)>0 else "miss"}">'
                f'{"✅"+str(int(sd.get(k,0)))+"pt" if sd.get(k,0)>0 else "—"}</span></td>'
                for k, _, _ in INDICATORS
            )
            html += f"""
                    <tr>
                        <td>{i}</td>
                        <td><strong>{r['code']}</strong></td>
                        <td style="text-align:left">{r['name']}</td>
                        <td><small>{r['sector']}</small></td>
                        <td class="{score_cls}">{sc:.0f}</td>
                        <td><span class="{bt_cls}">{wr:.1f}%（{r['backtest_sample']}回）</span></td>
                        {indicator_cells}
                    </tr>"""

        html += f"""
                </tbody>
            </table>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>⚠️ BackLog値はバックテストの参考値です。将来の利益を保証するものではありません。</p>
        <p style="margin-top:12px;">
            <a href="../index.html">🏠 トップ</a> |
            <a href="../reports/{date_str}.html">📊 Basicレポート</a> |
            <a href="../analysis/{date_str}.html">🔬 Analysisレポート</a> |
            <a href="../legal/disclaimer.html">⚠️ 免責事項</a>
        </p>
    </div>
</div>
<script>
    function sortTable(col) {{
        const table = document.getElementById("stockTable");
        const rows = Array.from(table.rows).slice(1);
        const isAsc = table.dataset.sortCol == col && table.dataset.sortDir == "asc";
        rows.sort((a, b) => {{
            let aVal = a.cells[col].textContent.trim().replace(/[^0-9.-]/g,'');
            let bVal = b.cells[col].textContent.trim().replace(/[^0-9.-]/g,'');
            aVal = parseFloat(aVal) || aVal; bVal = parseFloat(bVal) || bVal;
            return isAsc ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1);
        }});
        rows.forEach(row => table.tBodies[0].appendChild(row));
        table.dataset.sortCol = col;
        table.dataset.sortDir = isAsc ? "desc" : "asc";
    }}
    function filterTable() {{
        const input = document.getElementById("search").value.toUpperCase();
        const rows = document.getElementById("stockTable").getElementsByTagName("tr");
        for (let i = 1; i < rows.length; i++) {{
            const text = rows[i].cells[1].textContent + rows[i].cells[2].textContent;
            rows[i].style.display = text.toUpperCase().includes(input) ? "" : "none";
        }}
    }}
    function switchTab(name) {{
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('tab-' + name).classList.add('active');
        event.target.classList.add('active');
    }}
</script>
<button onclick="window.scrollTo({{top:0,behavior:'smooth'}})"
        style="position:fixed;bottom:24px;right:24px;z-index:9999;background:#667eea;color:white;border:none;border-radius:50%;width:48px;height:48px;font-size:1.4em;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;line-height:1;"
        title="トップへ戻る">↑</button>
</body>
</html>"""

        filepath.write_text(html, encoding='utf-8')
        print(f"✅ Premiumレポート生成: {filepath}")
        return f"premium/{filename}"



class AdvancedStockScreener:
    """
    高度な日本株スクリーニングクラス v2.0
    ─ yfinanceのみで動作する全指標を統合
    """

    def __init__(self,
                 min_volume: int = 1_000_000,
                 enable_backtest: bool = True,
                 min_score: float = 30.0):
        """
        Args:
            min_volume   : 最低30日平均売買代金（円）
            enable_backtest : バックテスト機能を有効化
            min_score    : スクリーニング通過の最低スコア（0〜100）
        """
        self.min_volume    = min_volume
        self.enable_backtest = enable_backtest
        self.min_score     = min_score
        self.results       = []
        self.sector_stats  = defaultdict(int)
        self.ti            = TechnicalIndicators()
        self.scorer        = ScoringEngine()

    def select_free_tier_stocks(self, results: List[Dict], count: int = 3) -> List[Dict]:
        """
        無料版用：中位スコア帯から多様性を持って選抜

        戦略:
          1. スコア50〜75の中位帯を抽出
          2. 流動性（安心感）でソート
          3. セクター重複を避けて選択
          4. 「とっておきは出さない」が、安定感は出す

        Args:
            results: 全スクリーニング結果（スコア順ソート済み）
            count: 選抜数

        Returns:
            選抜された銘柄リスト
        """
        # 中位スコア帯を抽出（50〜75点）
        mid_tier = [r for r in results if 50 <= r['total_score'] < 75]

        if not mid_tier:
            # 中位帯がない場合は全体から選ぶ
            mid_tier = results

        # 流動性でソート（信頼感・安心感を優先）
        mid_tier.sort(key=lambda x: x['avg_volume_30d'], reverse=True)

        # セクター重複を避けて選択
        selected = []
        used_sectors = set()

        for stock in mid_tier:
            if stock['sector'] not in used_sectors:
                selected.append(stock)
                used_sectors.add(stock['sector'])
                if len(selected) == count:
                    break

        # 件数に満たない場合は重複を許容して追加
        if len(selected) < count:
            for stock in mid_tier:
                if stock not in selected:
                    selected.append(stock)
                    if len(selected) == count:
                        break

        return selected

    # ─────────────────────────────────────────────
    #  銘柄リスト取得（既存ロジック維持）
    # ─────────────────────────────────────────────
    def get_jpx_stock_list(self) -> pd.DataFrame:
        """JPX銘柄リストをローカルCSVから読み込み（約3,700銘柄）"""
        print("📥 JPX銘柄リストを読み込み中...")
        
        csv_path = Path("data/jpx_stock_list.csv")
        
        try:
            if csv_path.exists():
                # ローカルCSVを読み込み
                stocks = pd.read_csv(csv_path, dtype={'code': str})
                print(f"✅ {len(stocks)}銘柄を読み込みました（JPX公式リスト）")
                
                # 市場別集計
                if 'market' in stocks.columns:
                    for market_type in ['プライム', 'スタンダード', 'グロース']:
                        count = len(stocks[stocks['market'].str.contains(market_type, na=False)])
                        if count > 0:
                            print(f"   - {market_type}: {count}銘柄")
                print()
                return stocks
            else:
                print(f"⚠️ CSVファイルが見つかりません: {csv_path}")
                print("📋 フォールバック: サンプルリストを使用\n")
                # _get_sample_stocks() の代わりに直接DataFrameを返す
                return pd.DataFrame({
                    'code': ['7203','8306','9984','6758','8001',
                             '9432','6861','7974','4063','4502'],
                    'name': ['トヨタ','三菱UFJ','ソフトバンクG','ソニーG','伊藤忠',
                             'NTT','キーエンス','任天堂','信越化学','武田薬品'],
                    'sector': ['輸送用機器','銀行','情報・通信','電気機器','卸売',
                               '情報・通信','電気機器','その他製品','化学','医薬品'],
                    'market': ['プライム']*10
                })
                
        except Exception as e:
            print(f"❌ CSV読み込みエラー: {e}")
            print("📋 フォールバック: サンプルリストを使用\n")
            # 同じくDataFrameを直接返す
            return pd.DataFrame({
                'code': ['7203','8306','9984','6758','8001',
                         '9432','6861','7974','4063','4502'],
                'name': ['トヨタ','三菱UFJ','ソフトバンクG','ソニーG','伊藤忠',
                         'NTT','キーエンス','任天堂','信越化学','武田薬品'],
                'sector': ['輸送用機器','銀行','情報・通信','電気機器','卸売',
                           '情報・通信','電気機器','その他製品','化学','医薬品'],
                'market': ['プライム']*10
            })
            
    # ─────────────────────────────────────────────
    #  既存メソッド（後方互換のため維持）
    # ─────────────────────────────────────────────
    def calculate_ma(self, prices: pd.Series, period: int) -> pd.Series:
        """移動平均線を計算（後方互換）"""
        return prices.rolling(window=period).mean()

    def is_ma_trending_up(self, ma: pd.Series, lookback: int = 5,
                          min_slope: float = 0.0001) -> bool:
        """MA上昇トレンド判定（後方互換）"""
        if len(ma.dropna()) < lookback:
            return False
        recent_ma = ma.dropna().iloc[-lookback:].values
        normalized = recent_ma / recent_ma[0]
        slope = np.polyfit(np.arange(lookback), normalized, 1)[0]
        return slope > min_slope

    # ─────────────────────────────────────────────
    #  バックテスト（既存ロジック維持・拡張）
    # ─────────────────────────────────────────────
    def detect_signal_dates(self, data: pd.DataFrame) -> List[str]:
        """過去シグナル発生日を検出（バックテスト用）"""
        signal_dates = []
        for i in range(MA_LONG, len(data)):
            current = data.iloc[i]
            bottom_cross = (current['Low'] <= current['MA200'] < current['Close'])
            golden_cross = False
            if i > 0:
                prev = data.iloc[i - 1]
                golden_cross = (prev['MA50'] < prev['MA100'] and
                                current['MA50'] >= current['MA100'])
            if bottom_cross or golden_cross:
                signal_dates.append(current.name.strftime('%Y-%m-%d'))
        return signal_dates

    def calculate_win_rate(self, data: pd.DataFrame, signal_dates: List[str],
                           forward_days: int = 5) -> Tuple[float, int, int]:
        """シグナル後勝率を計算（後方互換）"""
        if not signal_dates:
            return 0.0, 0, 0
        wins, total = 0, 0
        for sd in signal_dates:
            try:
                idx = data.index.get_loc(sd)
                if idx + forward_days < len(data):
                    if data['Close'].iloc[idx + forward_days] > data['Close'].iloc[idx]:
                        wins += 1
                    total += 1
            except (KeyError, ValueError):
                continue
        return (wins / total * 100) if total > 0 else 0.0, wins, total

    def calculate_volatility(self, data: pd.DataFrame, window: int = 20) -> float:
        """ボラティリティ（年率）を計算"""
        returns = data['Close'].pct_change()
        return returns.tail(window).std() * np.sqrt(252) * 100

    # ─────────────────────────────────────────────
    #  PBR割安判定（ticker.info から取得）
    # ─────────────────────────────────────────────
    def get_pbr_score(self, info: Dict) -> Tuple[bool, str]:
        """
        PBR割安判定（株価純資産倍率）
        - PBR < 0.5: 超割安
        - PBR 0.5〜1.0: 割安（シグナルON）
        - PBR >= 1.0: 割安でない

        Returns:
            (is_cheap: bool, label: str)
        """
        pbr = info.get('priceToBook')
        if pbr is None or pbr <= 0:
            return False, 'PBR:N/A'
        if pbr < 0.5:
            return True, f'PBR:{pbr:.2f}（超割安）'
        elif pbr < 1.0:
            return True, f'PBR:{pbr:.2f}（割安）'
        else:
            return False, f'PBR:{pbr:.2f}'

    # ─────────────────────────────────────────────
    #  メインスクリーニング
    # ─────────────────────────────────────────────
    def screen_stock(self, code: str, name: str, sector: str = "不明") -> Optional[Dict]:
        """個別銘柄スクリーニング（v2.0 全指標統合版）"""
        ticker_symbol = f"{code}.T"

        try:
            ticker = yf.Ticker(ticker_symbol)
            # バックテスト + 一目均衡表に十分なデータ確保（最低2年）
            data = ticker.history(period="2y")

            if data.empty or len(data) < MA_LONG:
                return None

            # ── 銘柄名・セクター補完 ──────────────────────────────────
            info = {}
            if name == code:
                try:
                    info = ticker.info
                    name   = info.get('longName') or info.get('shortName') or code
                    sector = info.get('sector') or info.get('industry') or '不明'
                except Exception:
                    pass
            else:
                try:
                    info = ticker.info
                except Exception:
                    pass

            # ── テクニカル指標を一括計算 ─────────────────────────────
            data = TechnicalIndicators.bollinger_bands(data)
            data = TechnicalIndicators.obv(data)
            data = TechnicalIndicators.volume_analysis(data)
            data = TechnicalIndicators.vwap_daily_approx(data)
            data = TechnicalIndicators.moving_averages(data)
            data = TechnicalIndicators.ichimoku(data)

            # MA50/100 は既存バックテスト用に追加
            data['MA50']  = data['Close'].rolling(50).mean()
            data['MA100'] = data['Close'].rolling(100).mean()

            # ── 流動性チェック ───────────────────────────────────────
            avg_volume_30d = data['Volume_Yen'].tail(30).mean()
            if avg_volume_30d < self.min_volume:
                return None

            latest = data.iloc[-1]
            prev   = data.iloc[-2] if len(data) >= 2 else latest

            # ── 既存シグナル ──────────────────────────────────────────
            ma200_above    = bool(latest['Close'] > latest['MA200'])
            ma200_trending = ma200_above and self.is_ma_trending_up(data['MA200'], lookback=20)
            bottom_cross   = bool(latest['Low'] <= latest['MA200'] < latest['Close'])
            golden_cross   = bool(prev['MA50'] < prev['MA100'] and
                                  latest['MA50'] >= latest['MA100'])

            # ── ボリンジャーバンドシグナル ────────────────────────────
            pct_b   = latest.get('BB_Pct_B', np.nan)
            bb_width = latest.get('BB_Width', np.nan)
            # 反発候補: %b <= 0.2 (下限付近) かつバンド幅が収縮していない
            bb_reversal    = (not np.isnan(pct_b)) and (pct_b <= 0.2)
            # ブレイクアウト候補: %b >= 1.0 (上限突破) かつ出来高急増
            bb_breakout    = (not np.isnan(pct_b)) and (pct_b >= 1.0)
            bb_signal      = bb_reversal or bb_breakout

            # %b の説明ラベル
            if np.isnan(pct_b):
                bb_label = "N/A"
            elif pct_b <= 0.0:
                bb_label = f"⬇下限割れ({pct_b:.2f})"
            elif pct_b <= 0.2:
                bb_label = f"📍下限付近({pct_b:.2f})"
            elif pct_b >= 1.0:
                bb_label = f"🚀上限突破({pct_b:.2f})"
            elif pct_b >= 0.8:
                bb_label = f"📈上限付近({pct_b:.2f})"
            else:
                bb_label = f"中間({pct_b:.2f})"

            # ── 出来高シグナル ───────────────────────────────────────
            vol_ratio_avg  = latest.get('Volume_Ratio_Avg', 1.0)
            vol_ratio_1d   = latest.get('Volume_Ratio_1d', 1.0)
            volume_surge   = bool(vol_ratio_avg >= 1.5)  # 30日平均の1.5倍以上

            # ── OBVシグナル ──────────────────────────────────────────
            obv_trend_up    = bool(latest.get('OBV_Trend_Up', False))
            obv_divergence  = bool(latest.get('OBV_Divergence', False))
            obv_signal      = obv_trend_up  # スコアにはトレンドを使用

            # ── 一目均衡表シグナル ────────────────────────────────────
            ichimoku_bullish     = bool(latest.get('Ichi_Bullish', False))
            above_cloud          = bool(latest.get('Ichi_Price_above_Cloud', False))
            in_cloud             = bool(latest.get('Ichi_Price_in_Cloud', False))
            cloud_thick          = latest.get('Ichi_Cloud_Thick', 0.0)

            if ichimoku_bullish:
                ichi_label = "🟢三役好転"
            elif above_cloud:
                ichi_label = "🔵雲の上"
            elif in_cloud:
                ichi_label = "🟡雲の中"
            else:
                ichi_label = "🔴雲の下"

            # ── 移動平均乖離率 ────────────────────────────────────────
            ma25_dev = latest.get('MA25_Dev', np.nan)
            ma75_dev = latest.get('MA75_Dev', np.nan)

            # ── VWAP ────────────────────────────────────────────────
            above_vwap = bool(latest.get('Above_VWAP', False))

            # ── PBR割安（ticker.info）────────────────────────────────
            pbr_cheap, pbr_label = self.get_pbr_score(info)

            # ── 総合スコア計算 ────────────────────────────────────────
            signals = {
                'ma_trend'        : ma200_trending,
                'golden_cross'    : golden_cross,
                'bottom_cross'    : bottom_cross,
                'bb_signal'       : bb_signal,
                'obv_trend'       : obv_signal,
                'ichimoku_cloud'  : above_cloud,
                'ichimoku_sanryo' : ichimoku_bullish,
                'volume_surge'    : volume_surge,
                'pbr_value'       : pbr_cheap,
            }
            total_score, score_detail = self.scorer.score(latest, signals)

            # ── スコアフィルタ ────────────────────────────────────────
            if total_score < self.min_score:
                return None

            # ── バックテスト（既存ロジック維持）─────────────────────
            win_rate, backtest_sample = 0.0, 0
            if self.enable_backtest:
                signal_dates = self.detect_signal_dates(data)
                win_rate, _, total_bt = self.calculate_win_rate(data, signal_dates)
                backtest_sample = total_bt

            # ── ボラティリティ & リスクタグ ──────────────────────────
            volatility = self.calculate_volatility(data)
            if avg_volume_30d >= 100_000_000:
                risk_tag = "🟢安定"
            elif avg_volume_30d >= 10_000_000:
                risk_tag = "🟡標準"
            else:
                risk_tag = "🔴冒険"

            # ── セクター統計更新 ──────────────────────────────────────
            self.sector_stats[sector] += 1

            return {
                # ── 基本情報 ──────────────────────────────────────────
                'code'              : code,
                'name'              : name,
                'sector'            : sector,
                'price'             : latest['Close'],
                'date'              : latest.name.strftime('%Y-%m-%d'),

                # ── 総合スコア ────────────────────────────────────────
                'total_score'       : total_score,
                'score_detail'      : score_detail,

                # ── 既存シグナル ──────────────────────────────────────
                'ma200_trend'       : '上昇' if ma200_trending else '横ばい/下落',
                'bottom_cross'      : '✅' if bottom_cross else '—',
                'golden_cross'      : '✅' if golden_cross else '—',

                # ── ボリンジャーバンド ────────────────────────────────
                'bb_pct_b'          : round(pct_b, 3) if not np.isnan(pct_b) else None,
                'bb_width'          : round(bb_width, 4) if not np.isnan(bb_width) else None,
                'bb_label'          : bb_label,
                'bb_reversal'       : '✅' if bb_reversal else '—',
                'bb_breakout'       : '✅' if bb_breakout else '—',

                # ── 出来高 ────────────────────────────────────────────
                'avg_volume_30d'    : avg_volume_30d,
                'volume_ratio_1d'   : round(vol_ratio_1d, 2),
                'volume_ratio_avg'  : round(vol_ratio_avg, 2),
                'volume_surge'      : '✅' if volume_surge else '—',

                # ── OBV ──────────────────────────────────────────────
                'obv_trend_up'      : '✅' if obv_trend_up else '—',
                'obv_divergence'    : '✅強気D' if obv_divergence else '—',

                # ── VWAP ──────────────────────────────────────────────
                'above_vwap'        : '✅' if above_vwap else '—',
                'vwap_approx'       : round(latest.get('VWAP_Approx', 0), 1),

                # ── 移動平均乖離率 ────────────────────────────────────
                'ma25_dev'          : round(ma25_dev, 2) if not np.isnan(ma25_dev) else None,
                'ma75_dev'          : round(ma75_dev, 2) if not np.isnan(ma75_dev) else None,

                # ── 一目均衡表 ────────────────────────────────────────
                'ichimoku_label'    : ichi_label,
                'ichimoku_bullish'  : '✅三役好転' if ichimoku_bullish else '—',
                'ichimoku_cloud'    : '✅' if above_cloud else '—',
                'cloud_thick_pct'   : round(cloud_thick, 2) if not np.isnan(cloud_thick) else None,

                # ── PBR割安 ──────────────────────────────────────────
                'pbr_info'          : pbr_label,
                'pbr_value'         : '✅' if pbr_cheap else '—',

                # ── リスク・バックテスト ──────────────────────────────
                'volatility'        : volatility,
                'risk_tag'          : risk_tag,
                'win_rate'          : win_rate,
                'backtest_sample'   : backtest_sample,
            }

        except Exception:
            return None

    # ─────────────────────────────────────────────
    #  全銘柄スキャン
    # ─────────────────────────────────────────────
    def scan_all_stocks(self, max_stocks: Optional[int] = None,
                        use_sample: bool = False) -> List[Dict]:
        """全銘柄スキャン"""
        print("📊 銘柄リストを取得中...")
        stocks_df = self._get_sample_stocks() if use_sample else self.get_jpx_stock_list()

        if max_stocks:
            stocks_df = stocks_df.head(max_stocks)

        total = len(stocks_df)
        print(f"🔍 {total}銘柄のスクリーニングを開始（最低スコア: {self.min_score}点）\n")

        results = []
        for idx, row in stocks_df.iterrows():
            code   = row['code']
            name   = row['name']
            sector = row.get('sector', '不明')

            if (idx + 1) % 50 == 0:
                print(f"進捗: {idx + 1}/{total} ({len(results)}銘柄合致)")

            result = self.screen_stock(code, name, sector)
            if result:
                results.append(result)
                print(f"  ✅ {code} {result['name']} "
                      f"[{sector}] スコア:{result['total_score']}点")

            time.sleep(0.5)

        print(f"\n✅ スキャン完了: {len(results)}銘柄が条件に合致")

        # 総合スコア → 勝率 の順でソート
        results.sort(key=lambda x: (x['total_score'], x['win_rate']), reverse=True)
        return results

    # ─────────────────────────────────────────────
    #  セクターレポート（既存維持）
    # ─────────────────────────────────────────────
    def generate_sector_report(self) -> str:
        """セクター別レポート生成"""
        if not self.sector_stats:
            return ""
        report = "\n📊 セクター別内訳:\n"
        for sector, count in sorted(self.sector_stats.items(),
                                     key=lambda x: x[1], reverse=True)[:5]:
            report += f"  • {sector}: {count}銘柄\n"
        return report


class AdvancedNotifier:
    """
    拡張通知クラス v3.0（3プラン対応）
    ─ プランに応じて通知内容を切り替え
    """

    def __init__(self, service: str = "slack", plan_mode: str = "free_beta"):
        """
        Args:
            service: 通知サービス（slack / discord）
            plan_mode: プランモード
                - "free_beta": 暫定無償版（3件+HTMLリンク）
                - "free": 正式無償版（3件のみ）
                - "basic": ベーシック（HTMLリンク重視）
                - "premium": プレミアム（HTMLリンク重視）
        """
        self.service         = service
        self.plan_mode       = plan_mode
        self.slack_webhook   = os.getenv("SLACK_WEBHOOK_URL")
        
        # Discord Webhook URLs（プラン別）
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")  # 無料版
        self.discord_webhook_basic = os.getenv("DISCORD_BASIC_WEBHOOK_URL")  # ベーシック
        self.discord_webhook_premium = os.getenv("DISCORD_PREMIUM_WEBHOOK_URL")  # プレミアム
        self.discord_webhook_analysis = os.getenv("DISCORD_ANALYSIS_WEBHOOK_URL")  # #analysis
        
        self.base_url        = os.getenv("REPORT_BASE_URL",
                                         "https://[username].github.io/stock-screener-reports")

    def format_message_free(self, selected: List[Dict], total_count: int,
                             html_path: str = "") -> str:
        """
        無料版通知メッセージ（選抜3件）

        Args:
            selected: 選抜された3銘柄
            total_count: 全該当銘柄数
            html_path: HTMLレポートのパス（free_betaモードのみ）
        """
        today = datetime.now().strftime('%Y年%m月%d日')

        if not selected:
            return (
                f"📊 日本株スクリーニング結果\n📅 {today}\n\n"
                "🔇 本日は条件に合致する銘柄がありませんでした。\n"
            )

        msg = (
            f"📊 日本株スクリーニング結果 v3.0\n"
            f"📅 {today}\n\n"
            f"🎯 本日 {total_count}銘柄が条件に合致しました\n\n"
            f"【今日の注目3銘柄】（中位×安定戦略）\n"
            f"{'─'*40}\n\n"
        )

        for i, r in enumerate(selected, 1):
            # シグナル要約
            signals = []
            if r['bb_reversal'] == '✅': signals.append('BB反発')
            if r['bb_breakout'] == '✅': signals.append('BBブレイク')
            if r['volume_surge'] == '✅': signals.append('出来高急増')
            if r['obv_trend_up'] == '✅': signals.append('OBV上昇')
            if r['ichimoku_bullish'] != '—': signals.append(r['ichimoku_label'])

            signal_str = " | ".join(signals) if signals else "安定推移"

            msg += (
                f"{i}. 【{r['code']}】{r['name']}\n"
                f"   ⭐ スコア: {r['total_score']:.0f}点  |  {r['sector']}\n"
                f"   💵 株価: ¥{r['price']:,.0f}  |  {r['risk_tag']}\n"
                f"   📊 {signal_str}\n\n"
            )

        msg += (
            f"{'─'*40}\n"
            f"💎 上位銘柄も見たい方は\n"
            f"   👉 ベーシックプラン ¥980/月\n"
            f"   👉 プレミアムプラン ¥1,980/月（チャート付き）\n"
        )

        return msg

    def format_message_full(self, results: List[Dict], sector_report: str = "",
                            html_path: str = "") -> str:
        """
        ベーシック・プレミアム用通知（HTMLリンク重視）

        Args:
            results: 全スクリーニング結果
            sector_report: セクター統計
            html_path: HTMLレポートのパス
        """
        today = datetime.now().strftime('%Y年%m月%d日')
        plan_label = "プレミアムプラン" if self.plan_mode == "premium" else "ベーシックプラン"

        if not results:
            return (
                f"📊 日本株スクリーニング結果\n📅 {today}\n\n"
                "🔇 本日は条件に合致する銘柄がありませんでした。\n"
            )

        # Top 5のサマリー
        msg = (
            f"📊 日本株スクリーニング結果 v3.0\n"
            f"📅 {today}  |  {plan_label}\n\n"
            f"🎯 本日 {len(results)}銘柄が条件に合致しました\n\n"
            f"【Top 5 ハイライト】\n"
            f"{'─'*40}\n\n"
        )

        for i, r in enumerate(results[:5], 1):
            # シグナル要約
            signals = []
            if r['bottom_cross'] == '✅': signals.append('底値クロス')
            if r['golden_cross'] == '✅': signals.append('GC')
            if r['bb_reversal'] == '✅': signals.append('BB反発')
            if r['bb_breakout'] == '✅': signals.append('BBブレイク')
            if r['volume_surge'] == '✅': signals.append('出来高急増')
            if r['obv_trend_up'] == '✅': signals.append('OBV↑')
            if r['ichimoku_bullish'] != '—': signals.append(r['ichimoku_label'])

            signal_str = " | ".join(signals) if signals else "－"

            # スコア内訳を表示
            score_detail = r.get('score_detail', {})
            detail_parts = []
            if score_detail.get('ma_trend', 0) > 0:
                detail_parts.append(f"MA200↑")
            if score_detail.get('golden_cross', 0) > 0:
                detail_parts.append(f"GC")
            if score_detail.get('bb_signal', 0) > 0:
                detail_parts.append(f"BB")
            if score_detail.get('ichimoku_cloud', 0) > 0:
                detail_parts.append("雲上")
            if score_detail.get('ichimoku_sanryo', 0) > 0:
                detail_parts.append("三役好転")
            if score_detail.get('obv_trend', 0) > 0:
                detail_parts.append(f"OBV")
            if score_detail.get('volume_surge', 0) > 0:
                detail_parts.append(f"出来高")

            score_breakdown = "（" + " + ".join(detail_parts) + "）" if detail_parts else ""

            msg += (
                f"{i}. 【{r['code']}】{r['name']}\n"
                f"   ⭐ スコア: {r['total_score']:.0f}点 {score_breakdown}\n"
                f"   💵 株価: ¥{r['price']:,.0f}  |  {r['sector']}\n"
                f"   📊 {signal_str}\n"
                f"   🎲 {r['risk_tag']}\n\n"
            )

        if len(results) > 5:
            msg += f"...他{len(results)-5}銘柄\n\n"

        # HTMLリンク（強調）
        msg += (
            f"{'─'*40}\n"
            f"📄 **全{len(results)}銘柄の詳細レポート**\n"
            f"   👉 {self.base_url}/{html_path}\n\n"
            f"   ✅ ソート・検索機能\n"
            f"   ✅ 全指標のスコア内訳\n"
            f"   ✅ セクター別集計\n\n"
        )

        # セクターレポート
        if sector_report:
            msg += sector_report + "\n"

        # プラン案内
        if self.plan_mode == "basic":
            msg += (
                f"{'─'*40}\n"
                f"💎 さらに詳しく分析したい方は\n"
                f"   👑 プレミアムプラン ¥1,980/月\n"
                f"   └ 30日分アーカイブ + チャート表示\n"
            )

        return msg

    def format_message_analysis(self, results: List[Dict], sector_report: str = "",
                                html_path: str = "") -> str:
        """#analysis チャンネル向け：セクター別集計 + スコア内訳詳細"""
        today = datetime.now().strftime('%Y年%m月%d日')

        # ETFを除外（コード1300-1699）
        def _is_etf(r):
            try:
                return 1300 <= int(r.get('code', '0')) <= 1699
            except (ValueError, TypeError):
                return False
        filtered = [r for r in results if not _is_etf(r)]

        msg = (
            f"📈 セクター別分析レポート\n"
            f"📅 {today}  |  対象 {len(filtered)}銘柄（ETF除く）\n"
            f"{'─'*40}\n\n"
        )

        # セクター別集計
        sector_counts = {}
        sector_avg_scores = {}
        _BLANK = {'', '-', '－', '—', '―', 'N/A', 'n/a', 'nan', 'None'}
        for r in filtered:
            raw = str(r.get('sector', '') or '').strip()
            sec = 'ETF他' if raw in _BLANK else raw
            sector_counts[sec] = sector_counts.get(sec, 0) + 1
            sector_avg_scores.setdefault(sec, []).append(r['total_score'])

        sorted_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)

        msg += "【セクター別 銘柄数】\n"
        for sec, count in sorted_sectors[:8]:
            avg = sum(sector_avg_scores[sec]) / len(sector_avg_scores[sec])
            bar = "█" * min(count, 10)
            msg += f"  {sec[:8]:<8} {bar} {count}銘柄（平均{avg:.0f}点）\n"

        msg += f"\n{'─'*40}\n"

        # シグナル別集計
        signal_labels = [
            ('golden_cross',    'ゴールデンクロス'),
            ('bb_reversal',     'BB反発'),
            ('bb_breakout',     'BBブレイク'),
            ('volume_surge',    '出来高急増'),
            ('obv_trend_up',    'OBV上昇'),
            ('ichimoku_cloud',  '雲の上'),
            ('ichimoku_bullish','三役好転'),
            ('pbr_value',       'PBR割安'),
        ]
        msg += "【シグナル別 該当数】\n"
        for key, label in signal_labels:
            count = sum(1 for r in filtered if r.get(key) == '✅')
            pct = count / len(filtered) * 100 if filtered else 0
            msg += f"  {label:<12}  {count}銘柄 ({pct:.0f}%)\n"

        msg += f"\n{'─'*40}\n"

        # 詳細レポートリンク
        if html_path:
            msg += (
                f"📄 詳細レポート（ソート・検索対応）\n"
                f"   👉 {self.base_url}/{html_path}\n\n"
            )

        return msg

    def format_message_premium(self, results: List[Dict], sector_report: str = "",
                               html_path: str = "") -> str:
        """プレミアム用通知（BackLog上位＋全指標内訳）"""
        today = datetime.now().strftime('%Y年%m月%d日')

        if not results:
            return (
                f"👑 プレミアムレポート\n📅 {today}\n\n"
                "🔇 本日は条件に合致する銘柄がありませんでした。\n"
            )

        # BackLog上位5（win_rate降順）
        backlog_top = sorted(results, key=lambda x: x.get('win_rate', 0), reverse=True)[:5]

        msg = (
            f"👑 プレミアムレポート\n"
            f"📅 {today}  |  対象 {len(results)}銘柄\n\n"
            f"【🗂️ BackLog Top5】（バックテスト参考値 降順）\n"
            f"{'─'*40}\n\n"
        )

        for i, r in enumerate(backlog_top, 1):
            sd = r.get('score_detail', {})
            hit_indicators = []
            label_map = {
                'ma_trend': 'MA200', 'golden_cross': 'GC', 'bottom_cross': '底値クロス',
                'bb_signal': 'BB', 'obv_trend': 'OBV',
                'ichimoku_cloud': '雲上', 'ichimoku_sanryo': '三役好転',
                'volume_surge': '出来高', 'pbr_value': 'PBR割安'
            }
            for key, label in label_map.items():
                if sd.get(key, 0) > 0:
                    hit_indicators.append(f"{label}({int(sd[key])}pt)")

            breakdown = " | ".join(hit_indicators) if hit_indicators else "－"
            msg += (
                f"{i}. 【{r['code']}】{r['name']}\n"
                f"   ⭐ スコア: {r['total_score']:.0f}点\n"
                f"   💵 株価: ¥{r['price']:,.0f}  |  {r['sector']}\n"
                f"   📊 内訳: {breakdown}\n"
                f"   📈 BackLog: {r['win_rate']:.1f}%（{r['backtest_sample']}回）\n\n"
            )

        msg += f"{'─'*40}\n"

        # セクターサマリー
        if sector_report:
            msg += sector_report + "\n"

        # レポートリンク
        if html_path:
            msg += (
                f"{'─'*40}\n"
                f"👑 プレミアムレポート（BackLog一覧＋アーカイブ）\n"
                f"   👉 {self.base_url}/{html_path}\n"
            )

        return msg

    def send_discord_analysis(self, message: str):
        """#analysis チャンネルへ送信"""
        webhook_url = self.discord_webhook_analysis
        if not webhook_url:
            print("⚠️ DISCORD_ANALYSIS_WEBHOOK_URL が設定されていません")
            return
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        for chunk in chunks:
            resp = requests.post(webhook_url, json={"content": chunk})
            print("✅ Discord送信完了 (#analysis)" if resp.status_code == 204
                  else f"❌ Discord送信失敗 (#analysis): {resp.status_code}")
            time.sleep(0.3)

    def send_slack(self, message: str):
        """Slack送信"""
        if not self.slack_webhook:
            print("⚠️ SLACK_WEBHOOK_URL が設定されていません")
            return
        resp = requests.post(self.slack_webhook, json={"text": message})
        print("✅ Slack送信完了" if resp.status_code == 200
              else f"❌ Slack失敗: {resp.status_code}")

    def _send_to_webhook(self, webhook_url: str, message: str, label: str):
        """指定WebhookへDiscordメッセージを送信（2000文字制限対応）"""
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        for chunk in chunks:
            resp = requests.post(webhook_url, json={"content": chunk})
            print(f"✅ Discord送信完了 ({label})" if resp.status_code == 204
                  else f"❌ Discord送信失敗 ({label}): {resp.status_code}")
            time.sleep(0.3)

    def notify_all_channels(self, results: List[Dict], selected: List[Dict],
                            sector_report: str = "", html_path: str = "",
                            analysis_html_path: str = "", premium_html_path: str = ""):
        """
        設定済みの全Webhookに通知を送る。
        Webhookが未設定のチャンネルはスキップ。
        プランの増減に関わらずこのメソッド1つで完結する。
        """
        # #daily-picks（無料版 3銘柄）
        if self.discord_webhook:
            print("\n📤 #daily-picks へ送信中...")
            msg = self.format_message_free(selected, len(results))
            print(msg)
            self._send_to_webhook(self.discord_webhook, msg, "#daily-picks")
        else:
            print("⚠️ DISCORD_WEBHOOK_URL 未設定 → #daily-picks スキップ")

        # #full-report（ベーシック Top5）
        if self.discord_webhook_basic:
            print("\n📤 #full-report へ送信中...")
            msg = self.format_message_full(results, sector_report, html_path)
            self._send_to_webhook(self.discord_webhook_basic, msg, "#full-report")
        else:
            print("⚠️ DISCORD_BASIC_WEBHOOK_URL 未設定 → #full-report スキップ")

        # #analysis（セクター別集計 + 8指標内訳レポートリンク）
        if self.discord_webhook_analysis:
            print("\n📤 #analysis へ送信中...")
            msg = self.format_message_analysis(results, sector_report, analysis_html_path)
            self._send_to_webhook(self.discord_webhook_analysis, msg, "#analysis")
        else:
            print("⚠️ DISCORD_ANALYSIS_WEBHOOK_URL 未設定 → #analysis スキップ")

        # #premium（BackLog付きレポート）
        if self.discord_webhook_premium:
            print("\n📤 #premium へ送信中...")
            msg = self.format_message_premium(results, sector_report, premium_html_path)
            self._send_to_webhook(self.discord_webhook_premium, msg, "#premium")
        else:
            print("⚠️ DISCORD_PREMIUM_WEBHOOK_URL 未設定 → #premium スキップ")

    def notify(self, results: List[Dict], selected: List[Dict] = None,
               sector_report: str = "", html_path: str = ""):
        """後方互換用（notify_all_channels を推奨）"""
        if selected is None:
            selected = []
        self.notify_all_channels(results, selected, sector_report, html_path)

def is_market_open() -> tuple:
    """
    東京証券取引所の開場日かどうかを判定
    
    Returns:
        tuple: (開場かどうか, 理由)
    """
    today = datetime.now()
    
    # 土曜日チェック
    if today.weekday() == 5:
        return False, "土曜日"
    
    # 日曜日チェック
    if today.weekday() == 6:
        return False, "日曜日"
    
    # 祝日チェック
    if jpholiday.is_holiday(today):
        holiday_name = jpholiday.is_holiday_name(today)
        return False, f"祝日（{holiday_name}）"
    
    # 年末年始の特別休場日（12/31, 1/2, 1/3）
    if (today.month == 12 and today.day == 31) or \
       (today.month == 1 and today.day in [2, 3]):
       return False, "年末年始休場"
    
    return True, ""


def main():
    """メイン実行関数 v3.0 Final（Discord）"""
    
    # 市場休場日チェック
    is_open, reason = is_market_open()
    if not is_open:
        today = datetime.now().strftime('%Y年%m月%d日')
        print(f"🔇 本日（{today}）は{reason}のため市場休場です")
        print("📊 スクリーニングは実行されません\n")
        
        # Discord に休場通知（オプション）
        notification_service = os.getenv("NOTIFICATION_SERVICE", "discord")
        if notification_service == "discord":
            discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
            if discord_webhook:
                try:
                    message = {
                        "content": f"📅 市場休場のお知らせ\n\n本日（{today}）は{reason}のため、"
                                   f"東京証券取引所は休場です。\n"
                                   f"スクリーニングは次回開場日に実行されます。"
                    }
                    requests.post(discord_webhook, json=message)
                    print("✅ Discord に休場通知を送信しました")
                except Exception as e:
                    print(f"⚠️  Discord 通知エラー: {e}")
        
        return
    
    print("🚀 日本市場全銘柄スクリーニング開始 v3.0 Final\n")
    print("📢 通知: Discord\n")  # SendGrid 削除

    # ─── 環境変数読み込み ─────────────────────────────────────
    notification_service = os.getenv("NOTIFICATION_SERVICE", "slack")
    plan_mode            = os.getenv("PLAN_MODE", "free_beta")
    max_stocks           = os.getenv("MAX_STOCKS")
    enable_backtest      = os.getenv("ENABLE_BACKTEST", "true").lower() == "true"
    min_score            = float(os.getenv("MIN_SCORE", "30"))
    use_sample           = os.getenv("USE_SAMPLE", "false").lower() == "true"
    output_dir           = os.getenv("OUTPUT_DIR", "docs")

    print(f"⚙️  プランモード: {plan_mode}")
    print(f"📢 通知サービス: {notification_service}")

    if max_stocks:
        max_stocks = int(max_stocks)
        print(f"⚠️  テストモード: {max_stocks}銘柄のみスキャン\n")

    # ─── スクリーニング実行 ───────────────────────────────────
    screener = AdvancedStockScreener(
        min_volume      = 1_000_000,
        enable_backtest = enable_backtest,
        min_score       = min_score,
    )
    results = screener.scan_all_stocks(max_stocks=max_stocks, use_sample=use_sample)

    if not results:
        print("\n🔇 条件に合致する銘柄がありませんでした")
        return

    # ─── セクターレポート生成 ─────────────────────────────────
    sector_report = screener.generate_sector_report()

    # ─── 全レポート生成（チャンネルごとに専用ファイル） ────────────────────────────────────
    selected = screener.select_free_tier_stocks(results, count=3)
    print(f"\n🎯 無料版選抜：{len(selected)}銘柄")
    for i, s in enumerate(selected, 1):
        print(f"  {i}. {s['code']} {s['name']} (スコア:{s['total_score']:.0f}点)")

    html_gen = HTMLReportGenerator(output_dir=output_dir)
    today_str = datetime.now().strftime('%Y-%m-%d')

    print("\n📄 レポート生成中...")
    html_path          = html_gen.generate_basic_report(results, today_str, sector_report)
    analysis_html_path = html_gen.generate_analysis_report(results, today_str)

    # Top5チャート生成（Premium Step1）
    chart_paths = html_gen.generate_charts_for_top5(results, today_str)

    # 統計グラフ生成（Premium Step2）
    print("\n📊 統計グラフ生成中...")
    stats_paths = html_gen.generate_stats_charts(results, today_str)

    premium_html_path  = html_gen.generate_premium_report(
        results, today_str, sector_report,
        chart_paths=chart_paths, stats_paths=stats_paths
    )

    # ─── 通知送信 ─────────────────────────────────────────────
    # Webhookが設定されているチャンネルに一括送信
    notifier = AdvancedNotifier(service=notification_service, plan_mode=plan_mode)
    notifier.notify_all_channels(
        results, selected, sector_report,
        html_path=html_path,
        analysis_html_path=analysis_html_path,
        premium_html_path=premium_html_path,
    )

    print("\n✅ 処理完了")


if __name__ == "__main__":
    main()
