# 📊 日本市場全銘柄自動スクリーニングシステム

完全無料で運用できる、日本株のテクニカル分析自動通知システムです。

## ✨ 機能

### 基本機能
- ✅ **200日移動平均線が上昇トレンド**の銘柄を自動検出
- ✅ **底値が200日線とクロス**した銘柄を検出
- ✅ **50日/100日線のゴールデンクロス**を検出
- ✅ Slack/Discordへの自動通知
- ✅ 流動性フィルタ（30日平均売買代金）
- ✅ リスクタグ付け（安定/標準/冒険）

### 高度な機能
- 📊 過去のシグナル発生後の勝率計算（実装済み・拡張可能）
- 🔇 該当銘柄ゼロの日は「静寂の通知」
- 💰 流動性による自動リスク分類

## 🚀 セットアップ（5分で完了）

### 1. GitHubリポジトリの準備

1. GitHubで新規リポジトリを作成（例: `japan-stock-screener`）
2. このコードをアップロード

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/japan-stock-screener.git
git push -u origin main
```

### 2. 通知設定（Slack または Discord）

#### Slackの場合

1. Slackワークスペースで [Incoming Webhooks](https://api.slack.com/messaging/webhooks) を作成
2. 通知先チャンネルを選択
3. Webhook URLをコピー

#### Discordの場合

1. Discordサーバーの設定 → 連携サービス → ウェブフックを作成
2. ウェブフックURLをコピー

### 3. GitHubのシークレット設定

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 「New repository secret」で以下を追加:

| Name | Value | 説明 |
|------|-------|------|
| `SLACK_WEBHOOK_URL` | `YOUR_WEBHOOK_URL` | Slack URL（Slack使用時） |
| `DISCORD_WEBHOOK_URL` | `YOUR_WEBHOOK_URL` | Discord URL（Discord使用時） |
| `NOTIFICATION_SERVICE` | `slack` または `discord` | 使用する通知サービス |

### 4. 動作確認

#### 手動実行でテスト

1. GitHubリポジトリの「Actions」タブ
2. 「Daily Stock Screening」を選択
3. 「Run workflow」→「Run workflow」ボタンをクリック
4. 数分待つと通知が届く

#### 自動実行のスケジュール

デフォルトで**平日17:00（日本時間）**に自動実行されます。

## 📁 ファイル構成

```
japan-stock-screener/
├── stock_screener.py          # メインスクリプト
├── stock_screener_advanced.py  # 拡張版（バックテスト機能）
├── requirements.txt            # Python依存パッケージ
├── .github/
│   └── workflows/
│       └── daily_screening.yml # GitHub Actions設定
└── README.md                   # このファイル
```

## ⚙️ カスタマイズ

### スクリーニング条件の調整

`stock_screener.py` の以下の部分を編集:

```python
# 最低売買代金の変更（デフォルト100万円）
screener = StockScreener(min_volume=1_000_000)

# 200日線の上昇トレンド判定期間（デフォルト5日）
def is_ma_trending_up(self, ma: pd.Series, lookback: int = 5):
```

### 実行スケジュールの変更

`.github/workflows/daily_screening.yml` を編集:

```yaml
schedule:
  # 日本時間18:00に変更する場合 (UTC 09:00)
  - cron: '0 9 * * 1-5'
```

## 📊 通知メッセージの例

```
📊 日本株スクリーニング結果
📅 2026年2月14日

🎯 3銘柄が条件に合致しました:

【7203】トヨタ自動車
💵 株価: ¥2,850
📈 200日線: 上昇
🔄 底値クロス: ✅
⭐ GC: —
🟢安定 流動性: ¥450.2億
```

## 🔧 トラブルシューティング

### 通知が届かない

1. GitHub Actionsの実行ログを確認
2. シークレットが正しく設定されているか確認
3. Webhook URLが有効か確認

### データ取得エラー

- Yahoo Financeのレート制限に引っかかった可能性
- `time.sleep(0.5)` の値を増やす（例: `1.0`）

## ⚠️ 免責事項

このツールは投資判断の補助を目的としています。投資は自己責任で行ってください。
本ツールの使用によって生じたいかなる損失についても、作成者は責任を負いません。

---

**Happy Trading! 📈**
