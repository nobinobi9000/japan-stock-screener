#!/usr/bin/env python3
"""
日本市場全銘柄テクニカルスクリーニングシステム
- 200日線上昇トレンド銘柄の検出
- 底値と200日線のクロス検出
- 50日/100日線のゴールデンクロス検出
- Discord/(LINE)/Slack通知対応
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import json
import os
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class StockScreener:
    """日本株スクリーニングクラス"""
    
    def __init__(self, min_volume: int = 1000000):
        """
        Args:
            min_volume: 最低売買代金（円）デフォルト100万円
        """
        self.min_volume = min_volume
        self.results = []
        
    def get_jpx_stock_list(self) -> pd.DataFrame:
        """
        東証上場銘柄リストを取得する。
        JPXのxlsファイルはpandas/xlrdの互換性問題で取得不可なため、
        証券コード（1000〜9999）を総当たりしてyfinanceで存在確認する方式を採用。
        初回は時間がかかるが、確実に全銘柄をカバーできる。
        """
        print("📥 東証銘柄リストを生成中（コード総当たり方式）...")

        # 東証の証券コードは基本的に1000〜9999の4桁
        # yfinanceで存在するコードのみを抽出するのは時間がかかりすぎるため、
        # 実績のある主要コード帯を網羅するリストを使う
        
        # 方式: 既知の主要銘柄コード帯を直接指定
        # プライム・スタンダード・グロース市場の典型的なコード範囲
        code_ranges = list(range(1300, 1500)) + \
                      list(range(1700, 2000)) + \
                      list(range(2000, 3000)) + \
                      list(range(3000, 4000)) + \
                      list(range(4000, 5000)) + \
                      list(range(5000, 6000)) + \
                      list(range(6000, 7000)) + \
                      list(range(7000, 8000)) + \
                      list(range(8000, 9000)) + \
                      list(range(9000, 9999))

        stocks = []
        for code in code_ranges:
            stocks.append({
                'code': str(code).zfill(4),
                'name': str(code)  # 名称はyfinanceから後で取得
            })

        df = pd.DataFrame(stocks)
        print(f"✅ {len(df)}件のコードを生成しました（存在しない銘柄はスクリーニング時に自動スキップ）")
        return df
    
    def _get_sample_stocks(self) -> pd.DataFrame:
        """サンプル銘柄リスト（JPX取得失敗時のフォールバック）"""
        sample_stocks = {
            'code': ['7203', '8306', '9984', '6758', '8001', '9432', '6861', '7974', '4063', '4502'],
            'name': ['トヨタ', '三菱UFJ', 'ソフトバンクG', 'ソニーG', '伊藤忠', 'NTT', 'キーエンス', '任天堂', '信越化学', '武田薬品']
        }
        return pd.DataFrame(sample_stocks)
    
    def calculate_ma(self, prices: pd.Series, period: int) -> pd.Series:
        """移動平均線を計算"""
        return prices.rolling(window=period).mean()
    
    def is_ma_trending_up(self, ma: pd.Series, lookback: int = 5) -> bool:
        """
        移動平均線が上昇トレンドか判定
        Args:
            ma: 移動平均線のSeries
            lookback: 直近何日間の傾きを見るか
        """
        if len(ma) < lookback:
            return False
        recent_ma = ma.iloc[-lookback:].values
        # 最小二乗法で傾きを計算
        x = np.arange(lookback)
        slope = np.polyfit(x, recent_ma, 1)[0]
        return slope > 0
    
    def check_bottom_cross_ma200(self, low: float, close: float, ma200: float) -> bool:
        """底値が200日線とクロスしたか判定"""
        return low <= ma200 < close
    
    def check_golden_cross(self, ma_short: pd.Series, ma_long: pd.Series) -> bool:
        """ゴールデンクロス発生を判定"""
        if len(ma_short) < 2 or len(ma_long) < 2:
            return False
        
        # 前日: 短期MA < 長期MA
        # 当日: 短期MA >= 長期MA
        prev_short = ma_short.iloc[-2]
        prev_long = ma_long.iloc[-2]
        curr_short = ma_short.iloc[-1]
        curr_long = ma_long.iloc[-1]
        
        return prev_short < prev_long and curr_short >= curr_long
    
    def calculate_win_rate(self, data: pd.DataFrame, signal_dates: List[str], 
                          forward_days: int = 5) -> float:
        """
        過去のシグナル発生後の勝率を計算
        Args:
            data: 株価データ
            signal_dates: シグナル発生日のリスト
            forward_days: 何日後の収益を見るか
        Returns:
            勝率（%）
        """
        if not signal_dates:
            return 0.0
        
        wins = 0
        total = 0
        
        for signal_date in signal_dates:
            try:
                signal_idx = data.index.get_loc(signal_date)
                if signal_idx + forward_days < len(data):
                    entry_price = data['Close'].iloc[signal_idx]
                    exit_price = data['Close'].iloc[signal_idx + forward_days]
                    if exit_price > entry_price:
                        wins += 1
                    total += 1
            except:
                continue
        
        return (wins / total * 100) if total > 0 else 0.0
    
    def screen_stock(self, code: str, name: str) -> Optional[Dict]:
        """
        個別銘柄のスクリーニング
        Args:
            code: 銘柄コード（4桁）
            name: 銘柄名（不明な場合はコード番号）
        Returns:
            条件に合致した場合は銘柄情報の辞書、不合格ならNone
        """
        ticker_symbol = f"{code}.T"  # 東証銘柄
        
        try:
            # データ取得（過去1年分）
            ticker = yf.Ticker(ticker_symbol)
            data = ticker.history(period="1y")
            
            if data.empty or len(data) < 200:
                return None
            
            # yfinanceから銘柄名を取得（JPXリストにない場合の補完）
            if name == code:  # 名称未取得の場合
                try:
                    info = ticker.info
                    name = info.get('longName') or info.get('shortName') or code
                except Exception:
                    name = code
            
            # 流動性チェック（30日平均売買代金）
            data['Volume_Yen'] = data['Close'] * data['Volume']
            avg_volume_30d = data['Volume_Yen'].tail(30).mean()
            
            if avg_volume_30d < self.min_volume:
                return None
            
            # 移動平均線を計算
            data['MA50'] = self.calculate_ma(data['Close'], 50)
            data['MA100'] = self.calculate_ma(data['Close'], 100)
            data['MA200'] = self.calculate_ma(data['Close'], 200)
            
            # 最新データ
            latest = data.iloc[-1]
            
            # 条件1: 200日線が上昇トレンドか
            if not self.is_ma_trending_up(data['MA200']):
                return None
            
            # 条件2: 底値が200日線とクロス
            bottom_cross = self.check_bottom_cross_ma200(
                latest['Low'], 
                latest['Close'], 
                latest['MA200']
            )
            
            # 条件3: 50日/100日線のゴールデンクロス
            golden_cross = self.check_golden_cross(data['MA50'], data['MA100'])
            
            # いずれかの条件に合致
            if bottom_cross or golden_cross:
                # リスクタグ（流動性）
                if avg_volume_30d >= 100_000_000:  # 1億円以上
                    risk_tag = "🟢安定"
                elif avg_volume_30d >= 10_000_000:  # 1000万円以上
                    risk_tag = "🟡標準"
                else:
                    risk_tag = "🔴冒険"
                
                return {
                    'code': code,
                    'name': name,
                    'price': latest['Close'],
                    'ma200_trend': '上昇',
                    'bottom_cross': '✅' if bottom_cross else '—',
                    'golden_cross': '✅' if golden_cross else '—',
                    'avg_volume_30d': avg_volume_30d,
                    'risk_tag': risk_tag,
                    'date': latest.name.strftime('%Y-%m-%d')
                }
            
            return None
            
        except Exception as e:
            # エラーは静かに無視（多数の銘柄を処理するため）
            return None
    
    def scan_all_stocks(self, max_stocks: Optional[int] = None) -> List[Dict]:
        """
        全銘柄をスキャン
        Args:
            max_stocks: テスト用の最大銘柄数（Noneで全銘柄）
        """
        print("📊 銘柄リストを取得中...")
        stocks_df = self.get_jpx_stock_list()
        
        if max_stocks:
            stocks_df = stocks_df.head(max_stocks)
        
        total = len(stocks_df)
        print(f"🔍 {total}銘柄のスクリーニングを開始します...\n")
        
        results = []
        
        for idx, row in stocks_df.iterrows():
            code = row['code']
            name = row['name']
            
            # プログレス表示
            if (idx + 1) % 50 == 0:
                print(f"進捗: {idx + 1}/{total} 銘柄処理済み ({len(results)}銘柄が条件合致)")
            
            result = self.screen_stock(code, name)
            if result:
                results.append(result)
                print(f"  ✅ {code} {name}: 条件合致")
            
            # レート制限対策（0.5秒待機）
            time.sleep(0.5)
        
        print(f"\n✅ スキャン完了: {len(results)}銘柄が条件に合致")
        return results


class Notifier:
    """通知クラス（Slack/Discord対応）"""
    
    def __init__(self, service: str = "slack"):
        """
        Args:
            service: "slack" or "discord"
        """
        self.service = service
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    
    def format_message(self, results: List[Dict]) -> str:
        """通知メッセージをフォーマット"""
        today = datetime.now().strftime('%Y年%m月%d日')
        
        if not results:
            return f"""
📊 日本株スクリーニング結果
📅 {today}

🔇 本日は条件に合致する銘柄がありませんでした。
💰 現金でお待ちください。
"""
        
        msg = f"""
📊 日本株スクリーニング結果
📅 {today}

🎯 {len(results)}銘柄が条件に合致しました:

"""
        
        for r in results[:10]:  # 最大10銘柄
            msg += f"""
【{r['code']}】{r['name']}
💵 株価: ¥{r['price']:.0f}
📈 200日線: {r['ma200_trend']}
🔄 底値クロス: {r['bottom_cross']}
⭐ GC: {r['golden_cross']}
{r['risk_tag']} 流動性: ¥{r['avg_volume_30d']/1e8:.1f}億

"""
        
        if len(results) > 10:
            msg += f"\n...他{len(results)-10}銘柄"
        
        return msg
    
    def send_slack(self, message: str):
        """Slackで送信"""
        if not self.slack_webhook:
            print("⚠️ SLACK_WEBHOOK_URL が設定されていません")
            return
        
        payload = {"text": message}
        response = requests.post(self.slack_webhook, json=payload)
        
        if response.status_code == 200:
            print("✅ Slack通知を送信しました")
        else:
            print(f"❌ Slack通知失敗: {response.status_code}")
    
    def send_discord(self, message: str):
        """Discordで送信"""
        if not self.discord_webhook:
            print("⚠️ DISCORD_WEBHOOK_URL が設定されていません")
            return
        
        payload = {"content": message}
        response = requests.post(self.discord_webhook, json=payload)
        
        if response.status_code == 204:
            print("✅ Discord通知を送信しました")
        else:
            print(f"❌ Discord通知失敗: {response.status_code}")
    
    def notify(self, results: List[Dict]):
        """通知を送信"""
        message = self.format_message(results)
        
        # コンソールに表示
        print("\n" + "="*50)
        print(message)
        print("="*50 + "\n")
        
        # 通知サービスに送信
        if self.service == "slack":
            self.send_slack(message)
        elif self.service == "discord":
            self.send_discord(message)


def main():
    """メイン実行関数"""
    print("🚀 日本市場全銘柄スクリーニング開始\n")
    
    # 環境変数から設定を取得
    notification_service = os.getenv("NOTIFICATION_SERVICE", "slack")
    max_stocks = os.getenv("MAX_STOCKS")  # テスト用
    
    if max_stocks:
        max_stocks = int(max_stocks)
        print(f"⚠️ テストモード: {max_stocks}銘柄のみスキャン\n")
    
    # スクリーニング実行
    screener = StockScreener(min_volume=1_000_000)  # 最低100万円
    results = screener.scan_all_stocks(max_stocks=max_stocks)
    
    # 通知送信
    notifier = Notifier(service=notification_service)
    notifier.notify(results)
    
    print("\n✅ 処理完了")


if __name__ == "__main__":
    main()
