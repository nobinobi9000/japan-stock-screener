# ===================================
# 日本株スクリーニング v3.0 実行
# ===================================

Write-Host "🚀 スクリーニング開始..." -ForegroundColor Cyan

# .env から環境変数読み込み
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#].+?)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$key" -Value $value
        }
    }
    Write-Host "✅ 環境変数読み込み完了" -ForegroundColor Green
} else {
    Write-Host "❌ .env ファイルが見つかりません" -ForegroundColor Red
    exit
}

# スクリーニング実行
python stock_screener_v3_multiplan.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "
📤 GitHub にプッシュ中..." -ForegroundColor Yellow
    git add -f docs/
    $date = Get-Date -Format "yyyy-MM-dd"
    git commit -m "Daily screening report $date"
    git push

    Write-Host "
✅ 完了！" -ForegroundColor Green
    Write-Host "📊 GitHub Pages: https://nobi-labo.com/japan-stock-screener/" -ForegroundColor Cyan
}
