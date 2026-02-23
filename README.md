# 📊 日本株スクリーニング v3.0

yfinanceベースのテクニカル分析で、毎朝有望銘柄をDiscord/メールで通知するシステム

## 🎯 機能

- ✅ 全銘柄テクニカルスクリーニング
- ✅ Discord 通知（無料版：3銘柄）
- ✅ HTMLレポート生成（GitHub Pages で公開）
- ✅ スコアリング（0〜100点）
- ✅ ボリンジャーバンド・OBV・一目均衡表 対応

## 📈 レポート

最新のスクリーニング結果:
https://nobinobi9000.github.io/japan-stock-screener/

## 🚀 使い方

\\\powershell
# .env ファイルに Webhook URL を設定
notepad .env

# 実行
.\run.ps1
\\\

## 📦 必要なパッケージ

\\\ash
pip install yfinance pandas numpy requests
\\\

## 🔧 環境変数

\\\
DISCORD_WEBHOOK_URL  # Discord Webhook URL
PLAN_MODE=free_beta  # プランモード
USE_SAMPLE=false     # 本番モード
\\\

---

**Version**: 3.0 Multi-Plan Edition  
**Last Updated**: 2025-02-18
