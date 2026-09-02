# INTEGRATION_MAP.md — 3アプリ統合連携マップ（信頼できる唯一の情報源）

> 対象アプリ: **japan-stock-screener** / **kabu-signal** / **Kabu-Note**
> 最終更新: 2026-09-02
> このファイルは3リポジトリの `docs/PROJECT_STATE.md`・`docs/INTEGRATION_NOTES.md`（計6ファイル）を統合して作成した。
> 各アプリの詳細（機能一覧・技術スタック・デプロイ手順等）は元の6ファイルを参照。本ファイルは**連携部分に特化**したサマリー。
> **今後すべてのセッションは、この3アプリのいずれかを触る前に本ファイルを必ず読むこと。**
> 内容を更新した場合は、3リポジトリすべての `docs/INTEGRATION_MAP.md` を同時に更新し、末尾の最終更新日を変えること（1リポジトリだけ更新すると本ファイルの目的そのものが壊れる）。

---

## 1. 全体像（誰が何を担当しているか）

```
┌────────────────────────────────────────────────────────────────────┐
│  japan-stock-screener（唯一のデータ取得元）                          │
│  公開URL: screener.nobi-labo.com（Vercel / webapp）                  │
│  役割: 東証全銘柄(約4,400)を毎営業日スキャンし、9指標+JVQMスコアを計算 │
│  実行: cloudflare-watchdog が16:30 JST起動（GH純正cronは信頼性問題で廃止）│
│                                                                       │
│  出力① docs/latest.json      → GitHub Pages（公開・無料枠のみ）      │
│  出力② screener_snapshots /                                         │
│         screener_stock_snapshots → Supabase（非公開・全銘柄詳細）    │
└───────────┬───────────────────────────────────┬─────────────────────┘
            │ ①を読む（現状CORSで壊れている）      │ ②を読む(service_role)
            ▼                                   ▼
┌───────────────────────────┐     ┌──────────────────────────────────┐
│  Kabu-Note（保有株管理PWA） │     │  kabu-signal（シグナル通知PWA）    │
│  公開URL: kabu.nobi-labo.com│     │  公開URL: signal.nobi-labo.com    │
│  役割: 保有銘柄・配当・優待の │     │  役割: JVQMスコア+適時開示を       │
│  記録。独自yfinance取得は    │     │  ユーザーのWL/保有銘柄と突合し     │
│  update_stocks.pyのみ許可    │     │  PWA Push通知を送信（21:00 JST実行）│
│                              │     │                                    │
│  書き込み: holdings/         │────▶│  読み取り(service_role):          │
│  watchlist（自分のテーブル） │     │  Kabu-Noteのholdings/watchlist    │
└───────────────────────────┘     └──────────────────────────────────┘

Supabase プロジェクト nhkgyipjeithytqqfuda を3アプリ全員が共有
（screener/webapp・kabu-signal・Kabu-Note）
```

| アプリ | 主担当領域 | 独自データ取得 | 公開URL |
|---|---|---|---|
| japan-stock-screener | 東証全銘柄スキャン・スコアリング（唯一のデータ取得元）、有料会員向けwebapp | yfinance（全銘柄） | screener.nobi-labo.com |
| Kabu-Note | 保有株・配当・優待の個人管理PWA | yfinance（**保有銘柄のみ**、原則2の例外） | kabu.nobi-labo.com |
| kabu-signal | シグナル判定・個人化PWA Push通知 | kabutan.jp スクレイピング（適時開示、原則2の例外） | signal.nobi-labo.com（未検証、§6参照） |

### 共通の絶対原則（3リポジトリのCLAUDE.mdに同一内容が配置）

1. 投資助言に該当する要素を一切作らない
2. 銘柄データ取得は screener のバッチのみ（例外: Kabu-Note の update_stocks.py、kabu-signal の kabutan.jp 適時開示取得）
3. 有料コンテンツ（全銘柄データ）を公開経路に置かない
4. 個人化通知を共有チャンネルに流さない
5. 沈黙による誤認を作らない（バッチ失敗時も明示通知）
6. ユーザーデータの分離（Supabase RLS必須）

---

## 2. 連携しているデータ／ファイル／APIの一覧表

| # | 発信元アプリ | 受信先アプリ | データの内容 | 形式 | 更新タイミング | 影響範囲 |
|---|---|---|---|---|---|---|
| 1 | japan-stock-screener | Kabu-Note | `docs/latest.json`（top3・sector_heatmap・market_summary） | GitHub Pages 公開JSON | 平日16:30〜17:00頃 | **⚠️現状CORSで壊れている（§6-1）**。Kabu-Noteの`ScreenerWidget.jsx`・`Market.jsx`が影響を受ける |
| 2 | japan-stock-screener | japan-stock-screener（webapp自身） | 同上（`raw.githubusercontent.com`経由） | サーバー側プロキシ | 同上 | 正常稼働中（CORS問題なし） |
| 3 | japan-stock-screener | kabu-signal | `screener_snapshots`（鮮度メタ情報） | Supabase テーブル（service_role） | 平日16:30起動、所要17〜30分 | `jvqm_screener.py`の鮮度ガードが読む |
| 4 | japan-stock-screener | kabu-signal | `screener_stock_snapshots`（全銘柄JVQM・テクニカル指標） | Supabase テーブル（service_role） | 同上 | `jvqm_screener.py`のcandidates生成の主データ |
| 5 | Kabu-Note | kabu-signal | `watchlist`（user_id, code） | Supabase テーブル（service_role） | リアルタイム（ユーザー操作時） | `user_matcher.py`の買いシグナル突合対象 |
| 6 | Kabu-Note | kabu-signal | `holdings`（user_id, code, cost_price） | Supabase テーブル（service_role） | リアルタイム | `user_matcher.py`の売りシグナル突合・損益アラート計算 |
| 7 | kabu-signal | （自分自身のみ） | `pnl_alert_settings`（閾値） | Supabase テーブル | ユーザーがkabu-signalの設定画面で入力 | Kabu-Note側UIは未実装。将来Kabu-Noteが書き込む可能性あり（§4） |
| 8 | kabu-signal | （自分自身のみ） | `push_subscriptions` | Supabase テーブル | Push購読時 | 他アプリは参照しない |
| 9 | japan-stock-screener(webapp) | Kabu-Note / kabu-signal（将来） | `account_entitlements`（plan: free/basic/premium） | Supabase テーブル | Stripe Webhook経由 | **3アプリで同一レコードを指しているか未検証（§6-5）** |

---

## 3. 「Aを変更したらBとCも変更が必要になる」ケース（機械的判定ルール）

### ルールA. `screener_stock_snapshots` / `screener_snapshots`（Supabase）のカラムを変更する場合

- **カラム追加**: 安全。kabu-signalは`select=*`で全カラム取得するため追加分は無視される
- **以下のカラムを削除・リネームする場合は、必ず `kabu-signal/screener/jvqm_screener.py` の `fetch_latest_snapshot()` を同時に修正すること**:
  `snapshot_date`, `is_incomplete`, `success_rate`, `code`, `name`, `close_price`, `jvqm_pbr`, `jvqm_roe`, `jvqm_fcf_yield`, `jvqm_beta`, `jvqm_dividend_yield`, `jvqm_score`, `momentum_12m`, `near_52w_high`, `dead_cross`, `ma200_breakdown`, `ichimoku_bearish`, `bb_lower_break`, `obv_downtrend`, `volume_surge_down`, `fetch_success`
- `fetch_success`列のクエリ条件（`?fetch_success=eq.true`）を変える場合、kabu-signal側のクエリパラメータも同時修正
- `is_incomplete`の判定ロジック（`SNAPSHOT_INCOMPLETE_THRESHOLD`）を変える場合、kabu-signalの鮮度ガードの閾値解釈も揃える

### ルールB. `docs/latest.json` のスキーマを変更する場合

- 以下を**すべて**同時に確認・修正すること:
  - `Kabu-Note/src/hooks/useScreenerData.js`（`data.top3` / `data.sector_heatmap`参照）
  - `Kabu-Note/src/components/ScreenerWidget.jsx`（`stock.code/name/score/risk_tag/sector`参照）
  - `Kabu-Note/src/pages/Market.jsx`（`s.name/avg_score/stock_count`参照）
  - `japan-stock-screener/webapp/lib/useScreenerData.ts`（同じキーを参照、**こちらは実際に本番稼働中**なので影響大）
- ※ただしKabu-Note側の経路自体が現状CORSで壊れている（§6-1）ため、Kabu-Note側の実害は限定的。webapp側は要注意

### ルールC. `watchlist` / `holdings`（Kabu-Note所有テーブル）のカラム構成を変更する場合

- `kabu-signal/screener/user_matcher.py` の以下の関数を同時に修正すること:
  - `fetch_user_code_map()`（`select=user_id,code`）
  - `fetch_holdings_cost_map()`（`select=user_id,code,cost_price`）
- `holdings.cost_price`の型を変更（numeric→text等）する場合も同様（`float()`変換が失敗する）

### ルールD. RLSポリシーを変更する場合

- `watchlist` / `holdings` / `screener_stock_snapshots` のRLSを「service_roleでも読めない」設定に変更すると、kabu-signalが全ユーザーデータ・全銘柄データを読めなくなり、**通知0件のまま沈黙する**（原則5違反のリスク）
- 変更前に必ずkabu-signalのservice_roleアクセスへの影響を確認すること

### ルールE. Supabaseプロジェクト（`nhkgyipjeithytqqfuda`）を移行・分離する場合

- 3アプリ全員（screener・kabu-signal・Kabu-Note）の環境変数を同時に更新する必要がある:
  - screener: GitHub Secrets の `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`
  - kabu-signal: Vercel環境変数 + GitHub Secrets の `NEXT_PUBLIC_SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`
  - Kabu-Note: `.env.local` / Vercel環境変数の `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`

### ルールF. バッチ実行時刻を変更する場合

- 順序は **screener（現在16:30 JST起動）→ kabu-signal（21:00 JST起動）** を必ず守ること。逆転すると前日データでシグナルが生成される、または鮮度ガード不合格で配信されない
- screenerの起動を21:00 JSTに近づける場合、余裕（現状約4.5時間）が縮まるため注意
- kabu-signal側を変更する場合、`.github/workflows/morning-scan.yml`のコメント記述（古い時刻を前提にした記述が残っている）も更新すること

### ルールG. `account_entitlements.plan` の値（free/basic/premium）を変更する場合

- `kabu-signal/lib/entitlement.ts` の判定ロジックを同時に修正すること
- Kabu-Note側が独自の`account_entitlements`行を持っている可能性があり（§6-5で要検証）、webapp発行分との関係が未確定なため、**変更前に3アプリが本当に同一レコードを参照しているか確認必須**

### ルールH. `pnl_alert_settings` のスキーマを変更する場合

- 現状Kabu-Note側にUIが無いため直接の影響は無いが、`kabu-signal/screener/user_matcher.py`の`fetch_pnl_alert_thresholds()`が期待するカラム名と一致させること
- 将来Kabu-Note側にUIを実装する際は、この段階でカラム名を固定してから着手すること

### ルールI. GitHub Pagesのカスタムドメイン（`docs/CNAME`）を変更・削除する場合

- 現状`screener.nobi-labo.com`は実質Vercel（webapp）が使用しており、`docs/CNAME`削除によるwebappへの影響は無い
- ただし削除すると`nobinobi9000.github.io/japan-stock-screener/*`への301リダイレクトが解消され、**Kabu-Noteの現行コード（§6-1、修正前の状態）がそのまま動くようになる副次効果がある**。恒久対応（Kabu-Note側のURL修正、ルールB）を優先すべきで、この暫定対応に頼らないこと

---

## 4. 他に影響を与えず単独で変更してよい部分

| アプリ | 変更してよい範囲 |
|---|---|
| Kabu-Note | `dividend_records` / `transactions` / `annual_summary` / `daily_history` / `profiles` / `split_events` / `yutai_records` の各テーブル（他アプリは一切参照しない）。UI・スタイル全般。`update_stocks.py`の内部ロジック（`stocks`テーブルの列名を変えない限り） |
| kabu-signal | `push_subscriptions`のスキーマ（Kabu-Noteは現状参照していない）。`tdnet_checker.py`のスクレイピング対象・ロジック（出力フォーマットが変わらない限り）。UI・スタイル全般。`pnl_alert_settings`のスキーマ（現状Kabu-Note側UIが無いため、§3ルールHの通り実質単独変更可） |
| japan-stock-screener | Discord通知設定・チャンネル構成。`HTMLReportGenerator`等の未使用コード。webappのStripe決済フロー内部実装（`account_entitlements`の値自体を変えない限り）。スコアリングアルゴリズムの内部計算（共有カラムの意味・型が変わらない限り） |

---

## 5. データフロー・タイムライン（平日、JST）

```
16:30   cloudflare-watchdog が japan-stock-screener を起動（1回目）
        └─ 17〜30分で完了 → Supabase (screener_snapshots / screener_stock_snapshots) UPSERT
                            → docs/latest.json commit & push

16:xx   Kabu-Note の update_stocks.py 実行（screenerとは独立、待たない）
        └─ stocks / daily_history / dividend_records を更新

18:30   cloudflare-watchdog: 1回目が未成功なら再起動（2回目）

20:00   cloudflare-watchdog: それでも未成功なら管理者にResendメールアラート

21:00   kabu-signal バッチ実行
        ├─ jvqm_screener.py: screener_snapshots で鮮度確認（不合格なら15分×3回リトライ）
        ├─ tdnet_checker.py: kabutan.jpから当日の適時開示取得
        ├─ user_matcher.py: Kabu-Noteのwatchlist/holdingsを参照して個別突合
        ├─ push_sender.py: /api/push/send へPOST
        └─ signals/latest.json commit & push
```

**Kabu-Noteフロントエンドがscreenerのデータを読むタイミング**: ユーザーがアプリを開いた時点（不定期）、1日1回localStorageキャッシュ。ただし§6-1の通り現状は取得に失敗する。

---

## 6. 要確認事項（矛盾点・情報不足箇所）

以下は6ファイルを突き合わせた結果判明した、**Phase 3着手前に解消すべき問題**。優先度付きで列挙する。

### 🔴 6-1. Kabu-Noteのscreener連携がCORSで本番破損している（最優先）

`Kabu-Note/src/hooks/useScreenerData.js`は`https://nobinobi9000.github.io/japan-stock-screener/latest.json`を直接fetchしているが、このURLは`screener.nobi-labo.com`（Vercel/webapp）へ301リダイレクトされ、CORSヘッダが無いためブラウザからのfetchは失敗する（2026-09-02 curl実測確認済み、japan-stock-screener側INTEGRATION_NOTES.md記載）。

- **影響**: Kabu-Noteの`ScreenerWidget.jsx`（ダッシュボード）・`Market.jsx`（市場マップ）が本番で機能していない可能性が高い
- **提案されている修正**（未適用）: `SCREENER_URL`を`https://raw.githubusercontent.com/nobinobi9000/japan-stock-screener/main/docs/latest.json`に変更（Kabu-Note側の1行修正、screener側の変更は不要）
- **要確認**: この修正を適用してよいか、ユーザーに確認して着手すべき

### 🔴 6-2. `screener_stock_snapshots`の欠落は「修正済み」ではなく、2026-09-02時点でも継続中（Supabase実データで検証済み）

**コミット日付**: `git log`で確認した`2ccb14d`（numpy.bool_/float64 JSONシリアライズ修正）の実際の日付は
**2026-08-22 21:36:39 +0900**。kabu-signalの`PROJECT_STATE.md`にある「2026-09-02にpush済み」という
記述は誤り（コミットはそれより10日以上前）。

**修正状況**: Supabaseへ直接クエリして`screener_snapshots`（メタ）と`screener_stock_snapshots`
（銘柄別詳細）を突き合わせた結果、**Aug22の修正後も欠落が断続的に発生し続けている**ことを確認した
（2026-09-02実施、`execute_sql`でのSELECT結果）:

| snapshot_date | `screener_snapshots`（メタ）| `screener_stock_snapshots`（銘柄別）|
|---|---|---|
| 2026-08-24〜26 | 存在（success_rate≈0.949, is_incomplete=false） | **存在**（各4,439行） |
| 2026-08-27 | 存在（success_rate=0.9489, is_incomplete=false） | **0行（欠落）** |
| 2026-08-28 | 存在（success_rate=0.9486, is_incomplete=false） | **0行（欠落）** |
| 2026-08-31 | 存在（success_rate=0.9493, is_incomplete=false） | **存在**（4,439行） |
| 2026-09-01 | 存在（success_rate=0.9493, is_incomplete=false） | **0行（欠落）** |

メタ行（`screener_snapshots`）は`is_incomplete=false`で毎日正常に見えるため、**kabu-signalの鮮度ガード
（`snapshot_date`と`is_incomplete`しか見ない）はこの欠落を検知できない**。実際には
`export_snapshot_to_supabase()`内の銘柄別バッチ送信（500件区切り、例外を握りつぶすtry/except内）が
日によって全滅しており、原因は特定できていない（numpy型変換だけが原因なら8/24-26で再発しないはずで、
Aug22の修正だけでは説明がつかない）。

**結論**: 「修正済み」ではなく**未解決の間欠的バグ**として扱うこと。次回バッチでの自然解消を待つ方針は
誤り。`export_snapshot_to_supabase()`の銘柄別バッチ送信部分（`stock_screener_v3_multiplan.py:3323`
付近）に、失敗時に握りつぶさず原因をDiscord等へ通知するログ強化が必要。

### 🟠 6-3. Kabu-Noteの `PROJECT_STATE.md` に誤記がある（他2アプリの資料で指摘済み）

Kabu-Noteの`PROJECT_STATE.md`5-4節「kabu-signalとの連携: 現状は直接の連携なし」は**誤り**。kabu-signalの`user_matcher.py`がKabu-Noteの`watchlist`/`holdings`をservice_roleキーで直接読んでいる（Kabu-Note側アプリコードを経由しないサーバー間連携のため見えにくい）。Kabu-Note側の`docs/PROJECT_STATE.md`の記述修正が必要。

### 🟡 6-4. バッチ実行時刻の記載が資料間で食い違っている

kabu-signalの`PROJECT_STATE.md`・`INTEGRATION_NOTES.md`は screener の実行時刻を「16:07 JST」と記載しているが、これは2026-08-29以前の値。GitHub純正cronの信頼性問題（最大11時間超の遅延・未発火）により`cloudflare-watchdog`（16:30起動・18:30リトライ）に置き換え済み（japan-stock-screener側で実測確認済み）。kabu-signal側の資料が未更新。

### ✅ 6-5. `account_entitlements` は3アプリで完全に同一のテーブル・同一レコードを参照している（2026-09-02 Supabase実データ・3リポジトリのコードで検証済み）

**検証方法と結果:**

1. `information_schema.tables`で確認 → `public.account_entitlements`という名前のテーブルは
   プロジェクト全体に**1つしか存在しない**（重複や別スキーマでの同名テーブルなし）
2. カラム構成: `id (uuid, NOT NULL)`, `plan (text, NOT NULL)`, `plan_source (text)`,
   `updated_at (timestamptz, NOT NULL)`
3. 3リポジトリのコードを実際に読み比べた結果、**クエリの形が一字一句同じロジック**だった:
   - `japan-stock-screener/webapp/lib/entitlement.ts`: `resolvePlan()`
   - `kabu-signal/lib/entitlement.ts`: `resolvePlan()`（コメントに「screener-snapshot Edge
     Functionと同じ規約」と明記）
   - `Kabu-Note/src/hooks/useEntitlement.js`: `useEntitlement()`
   - いずれも `supabase.from('account_entitlements').select('plan').eq('id', userId).maybeSingle()`
     で、行が無ければ`'free'`扱いという同一のフォールバック規約
   - 加えて`kabu-signal/screener/email_sender.py`の`fetch_pro_user_emails()`も
     `GET /rest/v1/account_entitlements?select=id&plan=in.(basic,premium)`で同テーブルを読む
     （有料会員向け障害通知メールの宛先取得用）
4. **書き込み元はwebapp（`webapp/app/api/stripe/webhook/route.ts`）のみ**。kabu-signal・Kabu-Note
   のコード全体を検索したが、このテーブルへの書き込み（insert/update/upsert）は見つからなかった
   （両者とも読み取り専用）
5. 現在の実データ: `account_entitlements`は**0行**（`auth.users`は5人登録済みだが、誰も
   Stripe決済を完了していないため全員が`plan_source`の無い"free"扱いのまま）。したがって
   実例レコードでの相互参照確認はできなかったが、テーブル・カラム・クエリ・認証基盤
   （同一Supabaseプロジェクト、同一`auth.users`）がすべて共通である以上、**行が作られた瞬間から
   3アプリは物理的に同じレコードを見る**ことは構造上確定している

**結論**: 3ファイルとも「未検証」としていたが、**設計上は完全に共有されている**ことを確認した。
残る懸念は「実際に課金ユーザーが発生した際に想定通り動くか」の実地テストのみ（Phase 3で
Stripeテストモードでの決済→3アプリでのプラン反映を1度通しで確認することを推奨）。

### 🟡 6-6. `signals/latest.json` のキー構造が二重管理

`jvqm_screener.py`は`signals`キーを出力、`main.py`は`final_signals`キーを出力。フロント（`app/api/signals/route.ts`, `app/page.tsx`）は`final_signals`を参照するため、鮮度ガード失敗時に`jvqm_screener.py`の出力のみ残ると表示が空になる（kabu-signal自身の既知バグ、他アプリへの影響は現状なし）。

### 🟢 6-7. その他の未検証項目

- kabu-signalの公開ドメインが本当に`signal.nobi-labo.com`か（japan-stock-screener側の監査では`kabu.nobi-labo.com`のみ実地確認、`signal.nobi-labo.com`は自己申告のまま）
- `screener-snapshot` Supabase Edge Functionのソースコードがどこにあるか不明（japan-stock-screenerリポジトリ内には存在しない）。Kabu-Note・kabu-signalからの実際の利用実績も未確認
- kabu-signalの`tdnet_checker.py`がTDnetではなくkabutan.jpをスクレイピングしている点は、CLAUDE.mdの原則2の文言（「TDnet適時開示のみ例外」）と実装が不一致。CLAUDE.md更新かコード修正のどちらかで整理が必要
- kabu-signalの`RESEND_API_KEY`がGitHub Secretsに未登録のため、鮮度ガード不合格時の障害通知メールが送信されない（実害は軽微、`send_failure_email()`はバッチを止めない設計）

---

*このファイルを更新した場合は、3リポジトリ（Kabu-Note / kabu-signal / japan-stock-screener）の `docs/INTEGRATION_MAP.md` を同時に更新し、末尾の最終更新日を変えること。*
