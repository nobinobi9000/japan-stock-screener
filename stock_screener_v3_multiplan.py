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
    'ma_trend'       : 15,   # MA200上昇
    'golden_cross'   : 10,   # ゴールデンクロス
    'bottom_cross'   : 10,   # 底値クロス
    'bb_signal'      : 15,   # BB位置 (反発 or ブレイクアウト)
    'obv_trend'      : 10,   # OBV上昇トレンド
    'ichimoku'       : 20,   # 一目均衡表 (雲上・好転)
    'volume_surge'   : 10,   # 出来高急増
    'short_squeeze'  : 10,   # 信用倍率スコア
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

        # ディレクトリ作成
        for d in [self.reports_dir, self.premium_dir, self.assets_dir]:
            d.mkdir(parents=True, exist_ok=True)

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
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 800px;
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
        }}
        tr:hover {{ background: #f8f9fa; }}
        
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
</body>
</html>
"""

        filepath.write_text(html, encoding='utf-8')
        print(f"✅ HTMLレポート生成: {filepath}")
        return f"reports/{filename}"



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
    #  信用倍率スコア（ticker.info から取得）
    # ─────────────────────────────────────────────
    def get_short_score(self, info: Dict) -> Tuple[float, str]:
        """
        信用倍率・ショート比率からスコアを計算

        - short_ratio     : 貸株残高 / 1日平均出来高（返済にかかる日数）
          → 高いほど売り方の「しこり」が大きい（ショートスクイーズ候補）
        - short_float_pct : Float株数に対するショート比率(%)

        Returns:
            (score 0〜1.0, 説明ラベル)
        """
        short_ratio = info.get('shortRatio')         # 例: 3.5 日
        short_float = info.get('shortPercentOfFloat')  # 例: 0.12 = 12%

        label_parts = []
        score = 0.0

        if short_ratio is not None:
            label_parts.append(f"ShortRatio:{short_ratio:.1f}日")
            # 5日以上 → しこり大 → スクイーズ期待
            if short_ratio >= 10:
                score += 1.0
            elif short_ratio >= 5:
                score += 0.6
            elif short_ratio >= 2:
                score += 0.3

        if short_float is not None:
            pct = short_float * 100 if short_float < 1 else short_float
            label_parts.append(f"ShortFloat:{pct:.1f}%")
            # 20%以上 → 高ショート → スクイーズ候補
            if pct >= 20:
                score = min(score + 1.0, 1.0)
            elif pct >= 10:
                score = min(score + 0.5, 1.0)

        if not label_parts:
            return 0.0, "N/A"

        return min(score, 1.0), " / ".join(label_parts)

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
            ma200_trending = self.is_ma_trending_up(data['MA200'])
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

            # ── 信用倍率（ticker.info）───────────────────────────────
            short_score_raw, short_label = self.get_short_score(info)
            short_squeeze = short_score_raw >= 0.5  # 50%以上でシグナル扱い

            # ── 総合スコア計算 ────────────────────────────────────────
            signals = {
                'ma_trend'      : ma200_trending,
                'golden_cross'  : golden_cross,
                'bottom_cross'  : bottom_cross,
                'bb_signal'     : bb_signal,
                'obv_trend'     : obv_signal,
                'ichimoku'      : ichimoku_bullish or above_cloud,
                'volume_surge'  : volume_surge,
                'short_squeeze' : short_squeeze,
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
                'cloud_thick_pct'   : round(cloud_thick, 2) if not np.isnan(cloud_thick) else None,

                # ── 信用倍率（info）──────────────────────────────────
                'short_info'        : short_label,
                'short_squeeze'     : '✅' if short_squeeze else '—',

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

        # free_betaモードの場合はHTMLリンクを追加
        if self.plan_mode == "free_beta" and html_path:
            msg += (
                f"{'─'*40}\n"
                f"📄 全{total_count}銘柄の詳細レポートはこちら\n"
                f"   {self.base_url}/{html_path}\n\n"
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
            if r['bottom_cross'] == '●': signals.append('底値クロス')
            if r['golden_cross'] == '●': signals.append('GC')
            if r['bb_reversal'] == '●': signals.append('BB反発')
            if r['bb_breakout'] == '●': signals.append('BBブレイク')
            if r['volume_surge'] == '●': signals.append('出来高急増')
            if r['obv_trend_up'] == '●': signals.append('OBV↑')
            if r['ichimoku_bullish'] != '－': signals.append(r['ichimoku_label'])

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
            if score_detail.get('ichimoku', 0) > 0:
                detail_parts.append(f"一目")
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
                f"   🎲 {r['risk_tag']}  |  BT参考: {r['win_rate']:.1f}%（{r['backtest_sample']}回）\n\n"
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

    def send_slack(self, message: str):
        """Slack送信"""
        if not self.slack_webhook:
            print("⚠️ SLACK_WEBHOOK_URL が設定されていません")
            return
        resp = requests.post(self.slack_webhook, json={"text": message})
        print("✅ Slack送信完了" if resp.status_code == 200
              else f"❌ Slack失敗: {resp.status_code}")

    def send_discord(self, message: str):
        """Discord送信（プラン別Webhook URL対応 + 2000文字制限対応）"""
        
        # プランに応じてWebhook URLを選択
        if self.plan_mode == "premium":
            webhook_url = self.discord_webhook_premium
            plan_label = "プレミアム"
        elif self.plan_mode == "basic":
            webhook_url = self.discord_webhook_basic
            plan_label = "ベーシック"
        else:  # free または free_beta
            webhook_url = self.discord_webhook
            plan_label = "無料版"
        
        if not webhook_url:
            print(f"⚠️ Discord Webhook URL が設定されていません (plan_mode: {self.plan_mode})")
            return
        
        # 2000文字制限のため分割送信
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        for chunk in chunks:
            resp = requests.post(webhook_url, json={"content": chunk})
            print(f"✅ Discord送信完了 ({plan_label})" if resp.status_code == 204
                  else f"❌ Discord送信失敗 ({plan_label}): {resp.status_code}")
            time.sleep(0.3)

    def notify(self, results: List[Dict], selected: List[Dict] = None,
               sector_report: str = "", html_path: str = ""):
        """
        通知を送信（プランに応じて切り替え）

        Args:
            results: 全スクリーニング結果
            selected: 無料版選抜銘柄（free/free_betaモードのみ）
            sector_report: セクター統計
            html_path: HTMLレポートのパス
        """
        # メッセージ生成
        if self.plan_mode in ["free", "free_beta"]:
            if selected is None:
                print("❌ エラー: 無料版モードでは selected が必要です")
                return
            message = self.format_message_free(selected, len(results), html_path)
        else:
            message = self.format_message_full(results, sector_report, html_path)

        # コンソール出力
        print("\n" + "=" * 50)
        print(message)
        print("=" * 50 + "\n")

        # Webhook送信
        if self.service == "slack":
            self.send_slack(message)
        elif self.service == "discord":
            self.send_discord(message)

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

    # ─── プランに応じた処理 ───────────────────────────────────
    html_path = ""
    selected = []

    if plan_mode in ["free", "free_beta"]:
        # 無料版：中位3件を選抜
        selected = screener.select_free_tier_stocks(results, count=3)
        print(f"\n🎯 無料版：{len(selected)}銘柄を選抜しました")
        for i, s in enumerate(selected, 1):
            print(f"  {i}. {s['code']} {s['name']} (スコア:{s['total_score']:.0f}点)")

    if plan_mode == "free_beta":
        # 暫定無償版：HTMLレポート生成
        print("\n📄 HTMLレポート生成中（暫定無償版）...")
        html_gen = HTMLReportGenerator(output_dir=output_dir)
        today = datetime.now().strftime('%Y-%m-%d')
        html_path = html_gen.generate_basic_report(results, today, sector_report)

    elif plan_mode == "basic":
        # ベーシック：HTMLレポート生成（当日のみ）
        print("\n📄 HTMLレポート生成中（ベーシック版）...")
        html_gen = HTMLReportGenerator(output_dir=output_dir)
        today = datetime.now().strftime('%Y-%m-%d')
        html_path = html_gen.generate_basic_report(results, today, sector_report)

    elif plan_mode == "premium":
        # プレミアム：30日分アーカイブ + チャート生成（将来実装）
        print("\n👑 プレミアム版は将来実装予定です")
        html_gen = HTMLReportGenerator(output_dir=output_dir)
        today = datetime.now().strftime('%Y-%m-%d')
        html_path = html_gen.generate_basic_report(results, today, sector_report)

    # ─── 通知送信 ─────────────────────────────────────────────
    notifier = AdvancedNotifier(service=notification_service, plan_mode=plan_mode)

    if plan_mode in ["free", "free_beta"]:
	# 無料版通知
        notifier.notify(results, selected=selected, sector_report=sector_report,
                        html_path=html_path)
	
	# ベーシック版通知も追加（free_betaモードの場合のみ）
        if plan_mode == "free_beta":
            print(f"\n📤 ベーシック版通知送信中 (plan_mode: basic)")
            notifier_basic = AdvancedNotifier(service=notification_service, plan_mode="basic")
            print(f"   notifier_basic.plan_mode = {notifier_basic.plan_mode}")
            print(f"   results数 = {len(results)}")
            print(f"   html_path = {html_path}")
            notifier_basic.notify(results, sector_report=sector_report, html_path=html_path)
    else:
        notifier.notify(results, sector_report=sector_report, html_path=html_path)

    print("\n✅ 処理完了")


if __name__ == "__main__":
    main()
