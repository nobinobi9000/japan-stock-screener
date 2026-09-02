# PROJECT_STATE.md — japan-stock-screener 現状ドキュメント

最終更新: 2026-09-02（別セッションのClaudeによる調査に基づき作成・2026-09-02に一部訂正）

このファイルは、このリポジトリを初めて見る開発者・AIセッションが**このファイルだけを読めば
プロジェクト全体を正しく再現・理解できる**ことを目的とした引き継ぎ資料です。
記述はすべて実際のコード（2026-08-29〜09-02時点の内容）を確認した上で書かれています。
コードと矛盾する記述を見つけた場合はコードを正としてこのファイルを更新してください。

---

## 1. プロジェクトの目的・概要

**日本株スクリーナー（japan-stock-screener）** は、東証全銘柄（ETF含む約4,400銘柄）を
毎営業日自動でテクニカルスキャンし、条件成立の事実表示のみを配信するサービス。

**公開URL: `https://screener.nobi-labo.com`（無料枠のみ、認証不要）**

> ⚠️ **2026-09-02訂正**: このドメインは現在**GitHub Pagesではなく`webapp/`（Next.js、Vercel）に
> CNAME/DNSが向いている**（`dig`で確認: `screener.nobi-labo.com` → Vercelのエイリアス、
> `curl`で確認: `Server: Vercel` / `X-Powered-By: Next.js`）。
> `docs/CNAME`ファイルには同じ文字列が残っているが、GitHub Pages側の設定としては
> **事実上無効（DNSがそちらを向いていない）**。`docs/index.html`は静的ファイルとして
> リポジトリには存在するが、実際にこのドメインでユーザーに見えることはない
> （4節・6節で詳述）。

nobi-labo が運営する3つの株関連サービス（本サービス / kabu-signal / Kabu Note）の中で、
**唯一「東証全銘柄の生データ取得・9指標判定・スコア計算」を行うバッチ**であり、
他2サービスはこのバッチが生成する日次スナップショットを読むだけ、という単一パイプライン構成の
起点になっている（詳細は5節）。

### 絶対原則（このプロジェクトの憲法）

`CLAUDE.md`（本リポジトリ直下。`kabu-signal`・`Kabu-Note`の各リポジトリにも同一内容が配置されている）に
6つの絶対原則が定義されており、実装判断はすべてこれに従う。要約:

| # | 原則 |
|---|---|
| 1 | 投資助言に該当する要素を一切作らない（推奨・勝率・利確ライン等の文言禁止、事実表示のみ） |
| 2 | 銘柄データの取得はスクリーナーのバッチ1箇所のみ。他サービスは独自に再取得しない（例外: kabu-signalのTDnet適時開示のみ） |
| 3 | 有料コンテンツ（全銘柄データ）を公開経路に置かない。無料公開は「厳選3銘柄＋市場サマリー」のみ |
| 4 | 個人化された通知を共有チャンネルに流さない（kabu-signalの通知はPWA push・メールのみ） |
| 5 | 沈黙による誤認を作らない（バッチ失敗・データ欠損時は必ず明示通知する） |
| 6 | ユーザーデータの分離（Supabase RLSでユーザー間分離必須） |

原則の全文・実装フェーズ計画は [`docs/実装指示プロンプト.md`](実装指示プロンプト.md) を参照。
ただし同ファイルは計画時点のもので、**Phase 3（統一アカウント）・Phase 4/5の一部項目は既に実装済み**
（詳細は3節）。フェーズ番号を鵜呑みにせず、必ずコード側の実態を優先すること。

---

## 2. ディレクトリ構成

```
japan-stock-screener/
├── stock_screener_v3_multiplan.py   ← 【本体】全ロジックがここに集約（3,587行）
├── stock_screener.py                ← 旧v1（未使用・レガシー。どこからも呼ばれていない）
├── requirements.txt                 ← Python依存パッケージ
├── run.ps1                          ← ローカル手動実行用スクリプト（.env読込→本体実行→git push）
├── users.json                       ← 未使用の古いサンプルファイル（どこからも参照されていない。削除候補）
├── .env                             ← ローカル実行用の環境変数（gitignore対象、Discord webhook等の実値を含む）
│
├── data/
│   └── jpx_stock_list.csv           ← スキャン対象銘柄マスタ（code,name,market,sector の4列、約4,400行）
│
├── scripts/
│   └── check_market_day.py          ← GitHub Actions用の軽量休場日判定（yfinance等の重い依存なし）
│
├── docs/                            ← GitHub Pages公開ディレクトリ（screener.nobi-labo.com の実体）
│   ├── CNAME                        ← "screener.nobi-labo.com"
│   ├── index.html                   ← 無料枠LP。手動メンテナンスの静的HTML（本体スクリプトからは生成されない）
│   ├── latest.json                  ← 【毎日自動更新】無料枠データ（厳選3銘柄+サマリー）。詳細は4節
│   ├── legal/
│   │   ├── terms.html / privacy.html / disclaimer.html / tokushoho.html
│   ├── 実装指示プロンプト.md          ← 3サービス共通の実装計画マスタードキュメント
│   └── PROJECT_STATE.md             ← 本ファイル
│
├── .github/workflows/
│   └── daily_screen.yml             ← GitHub Actions定義。詳細は8節
│
├── cloudflare-watchdog/             ← 【2026-08-29新設】GitHub Actions schedule代替の外部トリガー
│   ├── src/index.js                 ← Cloudflare Worker本体
│   ├── wrangler.toml                ← cron設定・環境変数
│   └── package.json
│
├── verification/jquants_check/      ← J-Quants API がバックテスト用途に使えるかの検証（完了・使い切り）
│   ├── config.py / fetch_jquants.py / fetch_yfinance.py / compare_prices.py
│   ├── compare_scores.py / report.py / run_verification.py
│   └── output/report.md             ← 検証結果レポート（2026-07-03生成）
│
└── webapp/                          ← 有料会員向けNext.js Webアプリ（詳細は3・5節）
    ├── app/
    │   ├── page.tsx + HomeClient.tsx    ← トップページ（無料枠表示 + プラン案内）
    │   ├── SamplePreview.tsx            ← 全銘柄分析ページの架空データサンプル表示
    │   ├── login/page.tsx               ← ログイン/新規登録（Supabase Auth）
    │   ├── analysis/                    ← 全銘柄分析ページ（basic/premiumのみ）
    │   │   ├── page.tsx / AnalysisTable.tsx / SectorBreakdown.tsx
    │   └── api/
    │       ├── free-latest/route.ts     ← docs/latest.json のサーバー側プロキシ（CORS回避）
    │       ├── snapshot/route.ts        ← Supabase Edge Function `screener-snapshot` への認証プロキシ
    │       └── stripe/
    │           ├── checkout/route.ts    ← Stripe Checkout Session作成
    │           ├── portal/route.ts      ← Stripe Billing Portal Session作成
    │           └── webhook/route.ts     ← Stripe Webhook受信（entitlement更新）
    ├── lib/
    │   ├── entitlement.ts               ← resolvePlan() / isPaidPlan()
    │   ├── stripe.ts                    ← Stripeクライアント
    │   └── supabase/{client,server,admin}.ts
    ├── proxy.ts                         ← Next.js 16のmiddleware相当。未ログインガード
    └── package.json
```

---

## 3. 主要機能一覧と実装状況

| 機能 | 状態 | 実装箇所 |
|---|---|---|
| 東証全銘柄スキャン（シャード分割・並列） | ✅完了 | `stock_screener_v3_multiplan.py` `scan_all_stocks()` / GH Actions matrix (10並列) |
| 9指標スコアリング（100点満点） | ✅完了 | `SCORE_WEIGHTS`（207行目）、`ScoringEngine.score()`（532行目） |
| 6種シグナルパターン自動分類 | ✅完了 | `classify_signal_pattern()`（223行目） |
| JVQM（Value-Quality-Momentum）スコア | ✅完了 | `calc_jvqm()`（265行目）。kabu-signal独自計算からの移管が完了済み（原則2） |
| 売り側6指標（デッドクロス等） | ✅完了 | `screen_stock()`内 `sell_signals`辞書（2329行目）。kabu-signal Phase5項目3に対応 |
| 無料枠配信（厳選3銘柄+サマリー、GitHub Pages） | ✅完了 | `export_json()`（2570行目）→ `docs/latest.json` |
| 全銘柄データの非公開Supabase配信（原則3） | ✅完了 | `export_snapshot_to_supabase()`（3233行目） |
| Discord通知（5チャンネル: daily-picks/full-report/analysis/premium/chart-analysis） | ✅完了（ただしHTMLリンク部分は空） | `AdvancedNotifier.notify_all_channels()`（3078行目） |
| 全銘柄HTMLレポート生成（basic/analysis/premium） | ⚠️**廃止済み（コードは残存・未呼出）** | `HTMLReportGenerator`クラス内の`generate_basic_report`等（829〜1943行目）。呼び出し箇所なし。原則3対応でSupabase配信に切替済み |
| データ取得失敗・0件時の明示通知（原則5） | ✅完了 | `_notify_and_record_empty_results()`（3390行目） |
| JPX営業日ゲート（祝日・年末年始） | ✅完了 | `scripts/check_market_day.py` / 本体側 `is_market_open()`（3159行目、二重実装） |
| 土曜キャッシュ更新ジョブ | ⚠️**部分的に無意味化**（6節参照） | `warm_cache_all_stocks()`（2450行目） |
| Webアプリ（無料枠LP + ログイン） | ✅完了・稼働中と思われる | `webapp/app/page.tsx`, `HomeClient.tsx` |
| Webアプリ（全銘柄分析ページ、basic/premium限定） | ✅完了 | `webapp/app/analysis/` |
| Supabase Auth（Kabu Note/kabu-signalと共通アカウント基盤） | ✅完了（Phase3相当） | `webapp/lib/supabase/*`, ログインページの文言に明記 |
| Stripe決済（Basicプラン ¥980/月） | ✅コード完了・**本番稼働は未確認** | `webapp/app/api/stripe/*`。LPには「βテスト期間中は全機能無料」と表示中 |
| Premiumプラン（30日アーカイブ等） | ❌未着手 | LP上「準備中」表示のみ |
| 外部トリガー監視（GitHub Actions schedule代替） | ✅完了・2026-08-29デプロイ済み | `cloudflare-watchdog/` |
| J-Quants API バックテスト活用検証 | ✅検証完了（移行はしていない） | `verification/jquants_check/`。結論は「バックテスト専用データ基盤としてJ-Quants採用の価値あり、本番の日次スクリーニングは引き続きyfinance」 |
| メール通知（ENABLE_EMAIL） | ❌未実装（envフラグのみ存在、常にfalse） | `.github/workflows/daily_screen.yml` の `ENABLE_EMAIL: false` |
| kabu-signal側の実装（本リポジトリ外） | 不明・未調査 | 本ドキュメントの対象外。存在は `screener-snapshot` Edge Functionの呼び出し元として推測されるのみ |

---

## 4. データ構造・スキーマ

### 4-1. `docs/latest.json`（無料枠・公開、毎日上書き）

```jsonc
{
  "date": "2026-08-28",
  "top3": [
    {
      "code": "6197", "name": "ソラスト", "score": 70.0,
      "price": 1118.0, "risk_tag": "🟡標準", "sector": "サービス業",
      "pattern": "⛩一目好転"
    }
    // ... 3件固定
  ],
  "sector_heatmap": [
    { "name": "鉄鋼", "avg_score": 48.3, "stock_count": 3 }
    // ... セクター数分（avg_score降順）
  ],
  "market_summary": {
    "total_scanned": 4439,        // ETF等含む全スキャン対象数
    "total_screened": 123,        // スコア30点以上に合致した数
    "gc_count": 12,
    "volume_surge_count": 45,
    "ichimoku_count": 8,
    "pattern_distribution": { "📊シグナル点灯": 80, "⛩一目好転": 8, ... },
    "auto_comment": "「銀行業」セクターの平均スコアが67点で最高。..."
  }
}
```
生成元: `export_json()`（`stock_screener_v3_multiplan.py:2570`）。`risk_tag`は
出来高規模に応じて 🟢安定(3億円以上)/🟡標準(1000万円以上)/🔴冒険(未満) の3段階。

### 4-2. Supabaseテーブル（非公開、本リポジトリには定義なし・コード上の書き込み内容から逆引き）

**`screener_snapshots`**（1日1行、upsert key: `snapshot_date`）

| カラム | 型（推定） | 説明 |
|---|---|---|
| snapshot_date | date | 主キー |
| schema_version | text | `SNAPSHOT_SCHEMA_VERSION = "1.0"` |
| generated_at | timestamptz | ISO8601 |
| total_scanned | int | 全スキャン対象数 |
| success_count | int | データ取得成功数 |
| success_rate | float | success_count/total_scanned |
| is_incomplete | bool | success_rate < `SNAPSHOT_INCOMPLETE_THRESHOLD`(0.7) |

**`screener_stock_snapshots`**（1日×銘柄で1行、upsert key: `snapshot_date,code`、500件ずつバッチ送信）

| カラム | 説明 |
|---|---|
| snapshot_date, code, name, sector, close_price, fetch_success | 基本情報 |
| ma_trend, golden_cross, bottom_cross, bb_signal, obv_trend, ichimoku_cloud, ichimoku_sanryo, volume_surge, pbr_value | 買い9指標（bool） |
| total_score | 0〜100点 |
| jvqm_pbr, jvqm_roe, jvqm_fcf_yield, jvqm_beta, jvqm_dividend_yield, jvqm_score, momentum_12m, near_52w_high | JVQM関連 |
| dead_cross, ma200_breakdown, ichimoku_bearish, bb_lower_break, obv_downtrend, volume_surge_down | 売り6指標（bool） |

書き込み元: `export_snapshot_to_supabase()`（`stock_screener_v3_multiplan.py:3233`）。
`name`カラムはNOT NULL制約があるため、コード側で必ず何らかの文字列にフォールバックしている（コメント参照）。

**`account_entitlements`**（webapp側から書き込み。列: `id`(=Supabase Auth user id), `plan`('free'|'basic'|'premium'), `plan_source`）
書き込み元: `webapp/app/api/stripe/webhook/route.ts`。読み取り元: `webapp/lib/entitlement.ts` の `resolvePlan()`。

**`account_external_identities`**（列: `user_id`, `provider`('stripe'固定), `external_id`(Stripe customer id)、unique制約: `user_id,provider`）
書き込み元・読み取り元: 同上 `stripe/webhook/route.ts`, `stripe/portal/route.ts`。

> ⚠️ 上記4テーブルの実際のDDL（型・制約・RLSポリシー）はSupabaseダッシュボード側にあり、
> 本リポジトリ内にマイグレーションファイルは存在しない。今後スキーマ変更する際は
> Supabase側を直接確認すること。

### 4-3. `data/jpx_stock_list.csv`

列: `code,name,market,sector`（ヘッダ行あり、UTF-8 BOM付き）。約4,400行。
`market`列は「プライム（内国株式）」「ETF・ETN」等の文字列。

### 4-4. シャード中間ファイル（GitHub Actions実行中のみ・リポジトリには残らない）

- `shard_output/shard_{N}.pkl` — 各シャードの結果（pickle）。集計ジョブが読み込んでマージ
- `cache/_info_shard{N}.json`, `cache/_info.json` — 土曜キャッシュ更新時の`ticker.info`断片・統合ファイル
- `cache/{code}.parquet` — 土曜キャッシュ更新時の2年分価格データ（**6節参照: 現状どこからも読まれていない**）

---

## 5. 外部とのインターフェース

### 5-1. API

| エンドポイント | 用途 | 認証 |
|---|---|---|
| `GET webapp: /api/free-latest` | `docs/latest.json`を`raw.githubusercontent.com`経由でサーバー側取得して返す（CORS回避） | 不要 |
| `GET webapp: /api/snapshot?date=YYYY-MM-DD` | Supabase Edge Function `screener-snapshot`（本リポジトリ外・場所不明）へBearerトークン付きでプロキシ | 要ログイン |
| `POST webapp: /api/stripe/checkout` | Stripe Checkout Session作成（`STRIPE_BASIC_PRICE_ID`固定） | 要ログイン |
| `POST webapp: /api/stripe/portal` | Stripe Billing Portal Session作成 | 要ログイン |
| `POST webapp: /api/stripe/webhook` | Stripeイベント受信。署名検証(`STRIPE_WEBHOOK_SECRET`)で真正性担保、ログイン不要経路として`proxy.ts`のPUBLIC_PATHSに登録 | Stripe署名検証 |
| Supabase REST `POST {SUPABASE_URL}/rest/v1/screener_snapshots` | バッチからのスナップショット書き込み | `SUPABASE_SERVICE_ROLE_KEY` |
| Supabase REST `POST {SUPABASE_URL}/rest/v1/screener_stock_snapshots` | 同上（銘柄別） | 同上 |
| GitHub REST `POST /repos/nobinobi9000/japan-stock-screener/actions/workflows/daily_screen.yml/dispatches` | cloudflare-watchdogからの起動 | GITHUB_TOKEN(fine-grained PAT) |
| Resend `POST https://api.resend.com/emails` | watchdogからの障害アラートメール | RESEND_API_KEY |

> ⚠️ `screener-snapshot` Supabase Edge Functionのソースコードは本リポジトリに存在しない。
> おそらくKabu NoteかSupabaseプロジェクト側で個別管理されている。次に触る際は要調査。

### 5-2. ファイル入出力

| ファイル | 更新タイミング | 更新者 |
|---|---|---|
| `docs/latest.json` | 平日営業日、集計ジョブ完了時 | GitHub Actions（`aggregate-screen`ジョブが`git commit && git push`） |
| `docs/index.html`, `docs/legal/*.html`, `docs/CNAME` | 手動編集のみ | 人間（Claude Codeセッション経由） |
| `cache/*.parquet`, `cache/_info.json` | 土曜のみ | GitHub Actions（`aggregate-cache-warm`ジョブが`actions/cache/save`） |

### 5-3. 他システムとの連携ポイント（Kabu Note / kabu-signal）

これは**原則2の実装そのもの**であり、本プロジェクトの中核的な設計。

1. **Kabu Note・kabu-signal は本リポジトリの株価データを独自に再取得しない**という契約が
   `CLAUDE.md`の原則2で明文化されている。データ取得はこのリポジトリのバッチのみが行う。
2. **無料層（3サービス共通で参照可能）**: `docs/latest.json`（GitHub Pages経由、認証不要）。
   webappの`useScreenerData.ts`がこれを消費しているのと同様、Kabu Note側も同じURLを
   参照していると推測されるが、Kabu Noteリポジトリ側のコードは未調査。
3. **有料層（認証必須）**: Supabase `screener_stock_snapshots`テーブルを、
   `screener-snapshot` Edge Function経由で配信。webappの`/api/snapshot`がこの実例。
   kabu-signalも同じテーブル・同じEdge Functionを読む設計のはず（`docs/実装指示プロンプト.md`
   Phase5より）だが、kabu-signal側の実装状況は本ドキュメント作成時点で未確認。
4. **JVQMスコア・売り側6指標**は元々kabu-signalが独自計算していたロジックを、
   このリポジトリの`calc_jvqm()`・`screen_stock()`内`sell_signals`に移管済み
   （`calc_jvqm()`のdocstringに「kabu-signal/screener/jvqm_screener.py の
   calc_jvqm_score()/check_momentum() と同一の計算式」と明記）。kabu-signal側は
   このスナップショットの列を読むだけになっているはず。
5. **統一アカウント（Supabase Auth）**: `account_entitlements`・`account_external_identities`
   テーブルはKabu Note/kabu-signalとの共通プロジェクトを前提に設計されている
   （`webapp/.env.example`のコメント「Supabase（kabu-note/kabu-signalと共通のプロジェクト）」)。
6. **Discord**: `#daily-picks`は全ユーザー共通内容の配信のみ（原則4）。kabu-signalの
   個人化通知はここには流れない設計（別チャンネル・PWA push・メールを使う想定、
   kabu-signal側コード未確認）。

---

## 6. 既知の不具合・技術的負債・保留中のTODO

1. **GitHub Actions native `schedule`トリガーの信頼性問題（2026-08-27発生・対応済み）**
   GitHub純正cronが最大11時間以上遅延・完全に未発火することが実測で確認された。
   `cloudflare-watchdog/`による外部トリガー（16:30/18:30/20:00 JST）に置き換え済み
   （`.github/workflows/daily_screen.yml`から平日分の`schedule:`を削除、`workflow_dispatch`のみ残存）。
   土曜のキャッシュ更新cron（`7 7 * * 6`）は未対応のまま残っている（同じリスクを抱える）。

2. **土曜キャッシュ更新の`.parquet`部分が死んでいる**
   `warm_cache_all_stocks()`（2450行目）は`cache/{code}.parquet`に2年分価格を書き込むが、
   リポジトリ全体を検索しても`read_parquet`の呼び出しが1件も無い。平日の`screen_stock()`は
   `get_full_stock_data()`→`ticker_history_2y()`で毎回yfinanceに直接フル取得しており、
   `.parquet`キャッシュは一切読まれていない（実際に使われているのは`cache/_info.json`の
   `ticker.info`メタデータ部分のみ）。約4,400銘柄分のparquet書き込み・GitHub Actions cache保存に
   毎週コストを払っているが恩恵が無い状態。削除するか、読み込み経路を復活させるか要判断。

3. **`verification/jquants_check/fetch_yfinance.py`が壊れている**
   `prod.get_cached_stock_data(code)`を呼び出しているが、この関数は本体側から既に削除されている
   （コメントに「2026-05-15〜07に導入していた差分キャッシュ方式」を廃止した旨の記載あり）。
   検証自体は完了済み(`output/report.md`)で再実行の予定は無いはずだが、もし再実行する場合は
   `get_full_stock_data(code)`を呼ぶよう修正が必要。

4. **HTMLReportGenerator の大部分が未使用コード**
   `generate_basic_report`/`generate_analysis_report`/`generate_premium_report`
   （829〜1943行目、約1,100行）はどこからも呼び出されていない。原則3対応でSupabase配信に
   切り替えた際に呼び出し側だけ外され、定義は残された状態。削除するかどうかは要判断
   （後方互換・参考実装として意図的に残している可能性もあるため、勝手に削除しないこと）。
   `matplotlib`/`mplfinance`（`requirements.txt`記載）もこの未使用コード内でのみ
   import・使用されており、実質的に不要な依存関係になっている。

5. **`stock_screener.py`（旧v1）・`users.json`は未使用**
   前者はどこからも import/実行されていないレガシーファイル。後者もコード内に参照なし。
   削除候補だが、削除前にユーザー確認を取ること（プロジェクトのCLAUDE.mdルールにより
   ファイル削除は要確認）。

6. **`webapp/`は`screener.nobi-labo.com`に実際にデプロイ・稼働中（2026-09-02確認）**
   `curl`/`dig`で実地確認済み: `screener.nobi-labo.com`はVercel上の`webapp/`を指しており、
   GitHub Pages（`docs/`）はこのドメインでは**もう使われていない**。
   一方で`docs/CNAME`ファイルは`screener.nobi-labo.com`のまま残っており、
   `docs/index.html`（静的LP）はどこからもリンクされない孤立ファイルになっている。
   **影響**: GitHub Pages自体（`https://nobinobi9000.github.io/japan-stock-screener/*`）への
   直接アクセスは、カスタムドメイン設定により`screener.nobi-labo.com`へ301リダイレクトされる
   （GitHub Pagesの仕様）。この301レスポンスにはCORSヘッダが無いため、
   **`docs/latest.json`をブラウザから旧URL(`nobinobi9000.github.io/...`)で直接fetchする
   実装はすべて壊れている**（詳細は`docs/INTEGRATION_NOTES.md`参照。Kabu Noteの
   `useScreenerData.js`がこれに該当し、実際に影響を受けている）。
   Stripeは`sk_test_`系のテストキー運用が前提（本番切替は財務局への事前照会完了後、と
   `docs/実装指示プロンプト.md`に明記）。

7. **Discordの5チャンネル中「詳細レポートへのリンク」が常に空**
   `#full-report`/`#analysis`/`#premium`/`#chart-analysis`向けメッセージは
   `html_path=""`で呼ばれるため、リンク行自体は`if html_path:`ガードで正しく省略される
   （壊れたリンクにはならない）が、そもそもリンクを掲載する意味がなくなっている。
   将来的にwebapp側のURLをリンク先として渡すよう改修する余地がある。

8. **`.env`に実際のDiscord Webhook URL等の秘密情報が平文で存在**
   `.gitignore`で除外されているためコミットはされていないが、ローカルファイルとして
   実値が残っている点は認識しておくこと（本ドキュメントには値を転記していない）。

9. **🔴 `export_snapshot_to_supabase()`の銘柄別データ書き込みが間欠的に全滅している（未解決）**
   `stock_screener_v3_multiplan.py:3233`の`export_snapshot_to_supabase()`は、`screener_snapshots`
   （メタ1行）への書き込みと`screener_stock_snapshots`（銘柄別、500件ずつバッチ送信・失敗を
   握りつぶすtry/except内）への書き込みが別処理になっている。2026-09-02にSupabaseへ直接
   クエリして確認したところ、**メタ行は`is_incomplete=false`で毎日正常に見えるにもかかわらず、
   銘柄別テーブルが特定の日だけ0行になる**現象が続いている（2026-08-27, 08-28, 09-01が該当。
   同じ期間の08-24〜26, 08-31は正常に4,439行ずつ入っている）。numpy型変換のJSONシリアライズ
   バグ修正（commit `2ccb14d`, 2026-08-22）はこの問題を解決していない
   （修正日以降も再発しているため）。原因未特定。kabu-signalの鮮度ガードは`screener_snapshots`
   の`is_incomplete`しか見ないため、**この欠落を検知できずに素通りしている**点が特に問題。
   `export_snapshot_to_supabase()`の銘柄別バッチ送信部分で、失敗時に握りつぶさず原因を
   ログ・通知に出すよう改修する必要がある（詳細は`docs/INTEGRATION_MAP.md` 6-2節）。

---

## 7. 使用技術・主要ライブラリ

### バッチ本体（Python、`requirements.txt`より）

| ライブラリ | バージョン指定 | 用途 |
|---|---|---|
| yfinance | >=0.2.32 | 株価データ取得 |
| pandas | >=2.0.0 | データ処理 |
| numpy | >=1.24.0 | 数値計算 |
| requests | >=2.31.0 | Discord Webhook / Supabase REST呼び出し |
| jpholiday | 指定なし | 日本の祝日判定 |
| pyarrow | >=12.0.0 | parquet読み書き |
| matplotlib, mplfinance | >=3.7.0 / >=0.12.10b0 | チャート生成用。呼び出し箇所は`HTMLReportGenerator`内（582・718行目付近）のみで、これも4節の未使用コードに含まれる＝実質未使用 |
| openpyxl | >=3.1.0 | Excel関連（用途未確認） |

Python 3.11（GitHub Actions側で指定）。ローカル動作確認では3.13/3.14系も使用歴あり
（`__pycache__`内に`.cpython-314.pyc`が存在）。

### webapp（Next.js、`webapp/package.json`より）

| パッケージ | バージョン |
|---|---|
| next | 16.2.1 |
| react / react-dom | 19.2.4 |
| @supabase/ssr | ^0.9.0 |
| @supabase/supabase-js | ^2.99.3 |
| stripe | ^22.3.1 |
| tailwindcss | ^4 |
| typescript | ^5 |

Next.js 16のApp Router使用。ミドルウェアは`middleware.ts`ではなく`proxy.ts`という
ファイル名になっている点に注意（Next.js 16での名称変更に対応済み）。

### cloudflare-watchdog（`cloudflare-watchdog/package.json`より）

| パッケージ | バージョン |
|---|---|
| wrangler | ^4.127.1（devDependencies） |

Cloudflare Workers（ESモジュール形式、`"type": "module"`）。外部依存なし（fetch/Intl等の
ビルトインAPIのみ使用）。

---

## 8. 起動方法・デプロイ方法・環境変数

### 8-1. バッチのローカル実行

```powershell
cd japan-stock-screener
notepad .env   # DISCORD_WEBHOOK_URL等を設定
pip install -r requirements.txt
.\run.ps1      # 実行→成功時は docs/ をgit add -f && commit && push まで自動で行う
```
`run.ps1`は`RUN_MODE`を設定しないため、`main()`内の`run_mode == "single"`分岐
（3503行目〜）が使われる＝シャード分割なしの単一プロセス実行。

### 8-2. 本番実行（GitHub Actions）

`.github/workflows/daily_screen.yml`。トリガーは**2026-08-29時点で以下のみ**:
- `schedule: cron '7 7 * * 6'`（土曜16:07 JST、キャッシュ更新）
- `workflow_dispatch`（`cloudflare-watchdog/`から平日16:30/18:30 JSTに呼ばれる。手動実行も可）

ジョブ構成:
1. `check-market`（JPX営業日ゲート、`scripts/check_market_day.py`）
2. `shard-screen`（`mode==screen`かつ`is_open==true`時のみ。matrix 10並列、`max-parallel: 2`）
3. `aggregate-screen`（全シャード結果マージ→Supabase保存→Discord通知→`docs/`をcommit&push）
4. `shard-cache-warm` / `aggregate-cache-warm`（`mode==cache_warm`＝土曜のみ）

環境変数（`aggregate-screen`ジョブより抜粋、実値はGitHub Secrets）:

```
DISCORD_WEBHOOK_URL / DISCORD_BASIC_WEBHOOK_URL / DISCORD_PREMIUM_WEBHOOK_URL /
DISCORD_ANALYSIS_WEBHOOK_URL / DISCORD_CHART_WEBHOOK_URL
NOTIFICATION_SERVICE=discord
PLAN_MODE=free_beta
ENABLE_EMAIL=false
OUTPUT_DIR=docs
REPORT_BASE_URL=https://screener.nobi-labo.com
RUN_MODE=aggregate_screen（or shard_screen 等）
SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
SHARD_TOTAL=10（env全体）
MIN_SCORE=30
ENABLE_BACKTEST=true
```

### 8-3. cloudflare-watchdog のデプロイ

```bash
cd cloudflare-watchdog
npm install
npx wrangler login
npx wrangler secret put GITHUB_TOKEN      # fine-grained PAT、対象repoのみ、Actions:Read and write
npx wrangler secret put RESEND_API_KEY
npx wrangler deploy
```
`wrangler.toml`の`[vars]`に`GITHUB_OWNER`/`GITHUB_REPO`/`WORKFLOW_FILE`/`WORKFLOW_REF`/
`ALERT_FROM_EMAIL`/`ALERT_TO_EMAIL`が平文で入っている（機密情報ではないため問題なし）。
`workers_dev = false`により公開HTTPルートを持たない（cronのみで動作する設計、5-1節参照）。

### 8-4. webapp のローカル実行・デプロイ

```bash
cd webapp
npm install
cp .env.example .env.local   # 実値を埋める
npm run dev                   # http://localhost:3000（.claude/launch.jsonでは3132指定）
```
必要な環境変数（`.env.example`より）:
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY   # サーバー側専用、NEXT_PUBLIC_を付けないこと
STRIPE_SECRET_KEY           # sk_test_系（本番未移行）
STRIPE_WEBHOOK_SECRET
STRIPE_BASIC_PRICE_ID
```
デプロイ方法は未確認（6節TODO参照）。nobi-labo他プロジェクトの慣例（プロジェクトルート
`CLAUDE.md`参照）に従えばVercelへの`vercel deploy --prod --yes`が有力だが、
このwebappディレクトリに対する実行実績は本ドキュメント作成時点で確認できていない。

### 8-5. verification/jquants_check の再実行（参考、通常は不要）

6節TODO3の修正（`get_cached_stock_data`→`get_full_stock_data`置換）をしない限り
`fetch_yfinance.py`はエラーになる。`.env`に`JQUANTS_API_KEY`が必要（要ローテーション済みキー）。
