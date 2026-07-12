#!/usr/bin/env python3
"""
GitHub Actions 用: JPX営業日ゲートジョブ

stock_screener_v3_multiplan.py の is_market_open() と同じ判定ロジック（土日・
jpholiday の祝日・年末年始休場）を、重い依存(yfinance/pandas等)を
インストールせずに実行するための軽量スクリプト。

判定ロジックを変更する場合は stock_screener_v3_multiplan.py の
is_market_open() と本ファイルの is_market_open() を両方更新すること。

出力:
  - GITHUB_OUTPUT に mode(screen|cache_warm), is_open(true|false) を書き込む
  - 休場日（screenモードのみ）は DISCORD_WEBHOOK_URL へ休場通知を送信する
"""

import os
from datetime import datetime

import jpholiday
import requests


def is_market_open(today: datetime) -> tuple:
    """東京証券取引所の開場日かどうかを判定"""
    if today.weekday() == 5:
        return False, "土曜日"
    if today.weekday() == 6:
        return False, "日曜日"
    if jpholiday.is_holiday(today):
        holiday_name = jpholiday.is_holiday_name(today)
        return False, f"祝日（{holiday_name}）"
    if (today.month == 12 and today.day == 31) or \
       (today.month == 1 and today.day in [2, 3]):
        return False, "年末年始休場"
    return True, ""


def main() -> None:
    today = datetime.now()

    if today.weekday() == 5:
        # 土曜は市場休場日判定を行わず、常にキャッシュ更新ジョブを実行する
        mode = "cache_warm"
        is_open, reason = True, ""
    else:
        mode = "screen"
        is_open, reason = is_market_open(today)

    print(f"mode={mode} is_open={is_open} reason={reason}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"mode={mode}\n")
            f.write(f"is_open={'true' if is_open else 'false'}\n")

    if mode == "screen" and not is_open:
        today_str = today.strftime('%Y年%m月%d日')
        print(f"🔇 本日（{today_str}）は{reason}のため市場休場です")
        discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        if discord_webhook:
            try:
                message = {
                    "content": f"📅 市場休場のお知らせ\n\n本日（{today_str}）は{reason}のため、"
                               f"東京証券取引所は休場です。\n"
                               f"スクリーニングは次回開場日に実行されます。"
                }
                requests.post(discord_webhook, json=message, timeout=10)
                print("✅ Discord に休場通知を送信しました")
            except Exception as e:
                print(f"⚠️  Discord 通知エラー: {e}")


if __name__ == "__main__":
    main()
