# INTEGRATION_MAP.md — 3アプリ統合連携マップ（信頼できる唯一の情報源）

> 対象アプリ: **japan-stock-screener** / **kabu-signal** / **Kabu-Note**
> 最終更新: 2026-09-02
> このファイルは3リポジトリの `docs/PROJECT_STATE.md`・`docs/INTEGRATION_NOTES.md`（計6ファイル）を統合して作成した。
> 各アプリの詳細（機能一覧・技術スタック・デプロイ手順等）は元の6ファイルを参照。本ファイルは**連携部分に特化**したサマリー。
> **今後すべてのセッションは、この3アプリのいずれかを触る前に本ファイルを必ず読むこと。**
> 内容を更新した場合は、3リポジトリすべての `docs/INTEGRATION_MAP.md` を同時に更新し、末尾の最終更新日を変えること（1リポジトリだけ更新すると本ファイルの目的そのものが壊れる）。

---

## 0. 運用ルール: 更新は `PROJECT_STATE.md` 経由（本ファイルへの直接編集は禁止）

**2026-09-02よりこのルールを適用。** 複数セッションが3アプリを並行して触るため、本ファイルへの
直接編集で競合・上書き事故が起きるのを避ける目的で、更新は必ず以下のフローを経由すること。

### 発見・変更した側（作業セッション）

3アプリ間の連携に影響する発見・変更（バグ修正、スキーマ変更、URL変更、検証結果など）を
した場合、**本ファイル（`INTEGRATION_MAP.md`）を直接編集しない**。代わりに、自分が作業した
リポジトリの `docs/PROJECT_STATE.md` に `## INTEGRATION_MAP.mdへの反映待ち` という見出しの
セクションを作り（無ければ新規作成、既にあれば末尾に追記）、そこに内容を記録する。

### 反映する側（次にこのファイルを読むセッション）

作業に着手する前に、3リポジトリ（Kabu-Note / kabu-signal / japan-stock-screener）の
`docs/PROJECT_STATE.md` それぞれで `## INTEGRATION_MAP.mdへの反映待ち` セクションの有無を確認する。
記載があれば:
1. 内容を検討し、本ファイルの該当箇所に反映する
2. 反映後、3リポジトリすべての `docs/INTEGRATION_MAP.md` を同一内容に更新し、それぞれでコミットする
3. 反映元の `PROJECT_STATE.md` 側の「反映待ち」セクションはクリアする（記述を削除する）

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
            │ ①を読む（raw.githubusercontent.com経由）│ ②を読む(service_role)
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
| 1 | japan-stock-screener | Kabu-Note | `docs/latest.json`（top3・sector_heatmap・market_summary） | `raw.githubusercontent.com` 公開JSON | 平日16:30〜17:00頃 | **✅修正済み（2026-09-02）**。useScreenerData.jsのURLをraw.githubusercontent.com経由に変更してCORS問題解消（commit `f16089d`） |
| 2 | japan-stock-screener | japan-stock-screener（webapp自身） | 同上（`raw.githubusercontent.com`経由） | サーバー側プロキシ | 同上 | 正常稼働中（CORS問題なし） |
| 3 | japan-stock-screener | kabu-signal | `screener_snapshots`（鮮度メタ情報） | Supabase テーブル（service_role） | 平日16:30起動、所要17〜30分 | `jvqm_screener.py`の鮮度ガードが読む。**⚠️ §6-2の間欠バグにより、このメタ行だけが正常でも銘柄別データが0行のケースがある点に注意** |
| 4 | japan-stock-screener | kabu-signal | `screener_stock_snapshots`（全銘柄JVQM・テクニカル指標） | Supabase テーブル（service_role） | 同上 | `jvqm_screener.py`のcandidates生成の主データ。**✅ §6-2: momentum_12mのゼロ除算等でNaN/Infinityが混入し全銘柄分が書き込まれない間欠バグは修正済み（commit `53b10af`）** |
| 5 | Kabu-Note | kabu-signal | `watchlist`（user_id, code） | Supabase テーブル（service_role） | リアルタイム（ユーザー操作時） | `user_matcher.py`の買いシグナル突合対象 |
| 6 | Kabu-Note | kabu-signal | `holdings`（user_id, code, cost_price） | Supabase テーブル（service_role） | リアルタイム | `user_matcher.py`の売りシグナル突合・損益アラート計算 |
| 7 | kabu-signal | （自分自身のみ） | `pnl_alert_settings`（閾値） | Supabase テーブル | ユーザーがkabu-signalの設定画面で入力 | Kabu-Note側UIは未実装。将来Kabu-Noteが書き込む可能性あり（§4） |
| 8 | kabu-signal | （自分自身のみ） | `push_subscriptions` | Supabase テーブル | Push購読時 | 他アプリは参照しない |
| 9 | japan-stock-screener(webapp) | Kabu-Note / kabu-signal | `account_entitlements`（plan: free/basic/premium） | Supabase テーブル | Stripe Webhook経由 | **✅検証済み（§6-5）**。3アプリとも同一テーブル・同一クエリロジックを使用 |

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
- Kabu-Note側の`useEntitlement.js`も同様に修正すること（§6-5の検証により、3アプリとも `supabase.from('account_entitlements').select('plan').eq('id', userId).maybeSingle()` で行が無ければ`'free'`扱いという同一クエリ・同一フォールバック規約であることを確認済み）

### ルールH. `pnl_alert_settings` のスキーマを変更する場合

- 現状Kabu-Note側にUIが無いため直接の影響は無いが、`kabu-signal/screener/user_matcher.py`の`fetch_pnl_alert_thresholds()`が期待するカラム名と一致させること
- 将来Kabu-Note側にUIを実装する際は、この段階でカラム名を固定してから着手すること

### ルールI. GitHub Pagesのカスタムドメイン（`docs/CNAME`）を変更・削除する場合

- 現状`screener.nobi-labo.com`は実質Vercel（webapp）が使用しており、`docs/CNAME`削除によるwebappへの影響は無い
- `docs/latest.json`の配信経路は現在`raw.githubusercontent.com`経由（§6-1の修正）なので、`docs/CNAME`の状態には依存しない

### ルールJ. `calc_jvqm()` およびJVQM関連フィールドの計算ロジックを変更する場合

- `momentum_12m` / `jvqm_pbr` / `jvqm_roe` / `jvqm_fcf_yield` / `jvqm_beta` / `jvqm_dividend_yield` は `export_snapshot_to_supabase()` で `_json_safe_float()`（NaN/Infinity→None正規化）を経由してから送信するよう修正済み（§6-2、commit `53b10af`）。この計算式に新しいフィールドを追加する場合も、必ず`_json_safe_float()`を通してから`stock_rows`に入れること（通さずに生値を渡すと、NaN/Infinity混入時にそのバッチのシリアライズが失敗する。バッチ単位のtry/exceptで他バッチへの被害は防げるが、そのバッチの銘柄は欠落する）

---

## 4. 他に影響を与えず単独で変更してよい部分

| アプリ | 変更してよい範囲 |
|---|---|
| Kabu-Note | `dividend_records` / `transactions` / `annual_summary` / `daily_history` / `profiles` / `split_events` / `yutai_records` の各テーブル（他アプリは一切参照しない）。UI・スタイル全般。`update_stocks.py`の内部ロジック（`stocks`テーブルの列名を変えない限り） |
| kabu-signal | `push_subscriptions`のスキーマ（Kabu-Noteは現状参照していない）。`tdnet_checker.py`のスクレイピング対象・ロジック（出力フォーマットが変わらない限り）。UI・スタイル全般。`pnl_alert_settings`のスキーマ（現状Kabu-Note側UIが無いため、§3ルールHの通り実質単独変更可） |
| japan-stock-screener | Discord通知設定・チャンネル構成。`HTMLReportGenerator`等の未使用コード。webappのStripe決済フロー内部実装（`account_entitlements`の値自体を変えない限り）。スコアリングアルゴリズムの内部計算（共有カラムの意味・型が変わらない限り。ただしJVQM関連は§3ルールJに注意） |

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

**Kabu-Noteフロントエンドがscreenerのデータを読むタイミング**: ユーザーがアプリを開いた時点（不定期）、1日1回localStorageキャッシュ。§6-1の修正（2026-09-02）により正常取得を確認済み。

**§6-2の間欠バグ（`screener_stock_snapshots`が0行になる）は2026-09-02、commit `53b10af`で修正済み**。

---

## 6. 要確認事項（矛盾点・情報不足箇所）

以下は6ファイルを突き合わせた結果判明した、**Phase 3着手前に解消すべき問題**。優先度付きで列挙する。

### ✅ 6-1. Kabu-Noteのscreener連携CORS問題 — **修正済み（2026-09-02）**

`Kabu-Note/src/hooks/useScreenerData.js` の `SCREENER_URL` を `raw.githubusercontent.com` 経由に変更し解消。

- **旧URL（破損）**: `https://nobinobi9000.github.io/japan-stock-screener/latest.json`
  → `screener.nobi-labo.com`（Vercel/webapp）へ301リダイレクト → CORSヘッダなし → fetch失敗
- **新URL（正常）**: `https://raw.githubusercontent.com/nobinobi9000/japan-stock-screener/main/docs/latest.json`
  → CORS `*` ヘッダあり → HTTP 200 正常取得（動作確認済み: top3×3件、sector_heatmap×34件）
- **コミット**: `f16089d`（Kabu-Note）

### ✅ 6-2. `screener_stock_snapshots`の間欠的欠落 — **修正済み（2026-09-02、commit `53b10af`）**

**確定原因**: `stock_screener_v3_multiplan.py`の`calc_jvqm()`（265行目）内、`momentum_12m`の計算
（314行目）にゼロ除算・NaNガードが無い:
```python
momentum_12m = round(float(close_1y.iloc[-1] / close_1y.iloc[0] - 1) * 100, 1)
```
`close_1y.iloc[0]`（252営業日前の終値）が0またはNaNの銘柄が1件でもあると`inf`/`nan`が発生する。
同様に`jvqm_pbr`/`jvqm_roe`/`jvqm_beta`/`jvqm_dividend_yield`もyfinanceの`info.get(...)`を
`is not None`チェックのみで通しており、yfinanceがNaN floatを返すケースはすり抜ける。

この値が`export_snapshot_to_supabase()`（3233行目）の`stock_rows`構築時に未サニタイズのまま
代入され（`close_price`/`total_score`は`float(x or 0)`でガードされているが、jvqm系5項目と
`momentum_12m`は生値のまま）、`requests.post(json=chunk)`が内部で呼ぶ
`json.dumps(json, allow_nan=False)`（`requests/models.py`のデフォルト挙動、2026-09-02に
ローカル再現テストで実際のエラーメッセージと一致することを確認済み）がNaN/Infinityの
シリアライズに失敗し、`requests.exceptions.InvalidJSONError: Out of range float values
are not JSON compliant`が発生する。**銘柄別バッチ送信ループ全体が1つのtry/exceptで
囲われている**ため、最初に不正な値を含むバッチで残り全バッチが中断され、その日は
`screener_stock_snapshots`が0行のまま終わる。一方`screener_snapshots`（メタ行）は
別処理として先に書き込み完了済みのため`is_incomplete=false`のまま残る＝
**メタは正常、銘柄別は0行という非対称な失敗**が生じる。

**実ログでの確認**（2026-09-02、`gh run view --log`で直接確認）:

| 日付 | GitHub Actions結果 | `screener_snapshots`（メタ）| `screener_stock_snapshots` | ログ内エラー |
|---|---|---|---|---|
| 08-24〜26 | success | 正常 | 正常（4,439行） | なし |
| 08-27 | success | 正常(is_incomplete=false) | **0行** | `❌ 銘柄別スナップショットの保存中にエラー: Out of range float values are not JSON compliant` |
| 08-28 | success | 正常(is_incomplete=false) | **0行** | 同上 |
| 08-31 | success | 正常 | 正常（4,439行） | なし（`✅ ...失敗batch0件`） |
| 09-01 | success（shard10個全成功、41秒で完了、16:30定刻起動） | 正常(is_incomplete=false) | **0行** | 同上 |

09-01はタイムアウト・同時実行・cron遅延と一切無関係（定刻起動・全shard成功・短時間完了）に
発生しており、**純粋にその日のyfinanceデータ内容（特定銘柄のNaN/Inf値）に依存する
再現性バグ**と判断できる。numpy型変換バグ修正（commit `2ccb14d`、実際の日付は2026-08-22）は
本件とは別原因であり、修正後も再発するのは当然だった。

**kabu-signalへの影響**: 鮮度ガードは`screener_snapshots.is_incomplete`しか見ないため、
この欠落を検知できず素通りする（原則5の趣旨に反する）。

**実施した修正**（2026-09-02、commit `53b10af`。詳細は`japan-stock-screener/docs/PROJECT_STATE.md`
6節-9項参照）:
1. `calc_jvqm()`の`momentum_12m`計算にNaN/Infinity/ゼロ除算ガードを追加
2. `export_snapshot_to_supabase()`でjvqm系全フィールドを`_json_safe_float()`
   （NaN/Infinity→None正規化）経由で送信するよう変更
3. バッチ送信をバッチ単位のtry/exceptに変更（1バッチの失敗が残り全バッチを
   道連れにしなくなった）
4. バッチ失敗時にDiscordへ通知する`_notify_snapshot_batch_failure()`を追加

合成データ（NaN/Infinityを含む1200銘柄）での再現テストにより、修正前なら0バッチ送信に
なる条件で全3バッチが正常送信されること、および1バッチが本物のネットワーク例外で
失敗しても残りのバッチは正常に送信されることを確認済み。過去の不良日の実データは
GitHub Actions artifactのretention-days:1により既に失効しているため、合成データでの
代替検証とした。

### ✅ 6-3. Kabu-Noteの `PROJECT_STATE.md` の誤記 — **修正済み**

Kabu-Noteの`PROJECT_STATE.md`5-4節は、kabu-signalの`user_matcher.py`がKabu-Noteの
`watchlist`/`holdings`をservice_roleキーで直接読んでいる旨（アプリコードを経由しない
サーバー間連携）を正しく記載する内容に更新済み。

### 🟡 6-4. バッチ実行時刻の記載が資料間で食い違っている

kabu-signalの`PROJECT_STATE.md`・`INTEGRATION_NOTES.md`は screener の実行時刻を「16:07 JST」と記載しているが、これは2026-08-29以前の値。GitHub純正cronの信頼性問題（最大11時間超の遅延・未発火）により`cloudflare-watchdog`（16:30起動・18:30リトライ）に置き換え済み（japan-stock-screener側で実測確認済み）。kabu-signal側の資料が未更新。

### ✅ 6-5. `account_entitlements` の3アプリ共有 — **検証済み（2026-09-02）**

`information_schema.tables`確認・3リポジトリのコード読み比べ・Supabase実データ確認の結果、
`public.account_entitlements`はプロジェクト全体に1つしか存在せず、3アプリとも同一の
クエリロジック（`select('plan').eq('id', userId).maybeSingle()`、行なしは`'free'`扱い）を
使用していることを確認。書き込み元はwebappの`stripe/webhook/route.ts`のみで、
kabu-signal・Kabu-Noteは読み取り専用。設計上、3アプリは物理的に同じレコードを見る構成。
残る懸念は実際の課金ユーザー発生時の実地テストのみ。

### 🟡 6-6. `signals/latest.json` のキー構造が二重管理

`jvqm_screener.py`は`signals`キーを出力、`main.py`は`final_signals`キーを出力。フロント（`app/api/signals/route.ts`, `app/page.tsx`）は`final_signals`を参照するため、鮮度ガード失敗時に`jvqm_screener.py`の出力のみ残ると表示が空になる（kabu-signal自身の既知バグ、他アプリへの影響は現状なし）。

### 🟢 6-7. その他の未検証項目

- kabu-signalの公開ドメインが本当に`signal.nobi-labo.com`か（japan-stock-screener側の監査では`kabu.nobi-labo.com`のみ実地確認、`signal.nobi-labo.com`は自己申告のまま）
- `screener-snapshot` Supabase Edge Functionのソースコードがどこにあるか不明（japan-stock-screenerリポジトリ内には存在しない）。Kabu-Note・kabu-signalからの実際の利用実績も未確認
- kabu-signalの`tdnet_checker.py`がTDnetではなくkabutan.jpをスクレイピングしている点は、CLAUDE.mdの原則2の文言（「TDnet適時開示のみ例外」）と実装が不一致。CLAUDE.md更新かコード修正のどちらかで整理が必要
- kabu-signalの`RESEND_API_KEY`がGitHub Secretsに未登録のため、鮮度ガード不合格時の障害通知メールが送信されない（実害は軽微、`send_failure_email()`はバッチを止めない設計）

---

*このファイルを更新した場合は、3リポジトリ（Kabu-Note / kabu-signal / japan-stock-screener）の `docs/INTEGRATION_MAP.md` を同時に更新し、末尾の最終更新日を変えること。*
