# INTEGRATION_NOTES.md — japan-stock-screener 連携ノート

最終更新: 2026-09-02

このファイルは **japan-stock-screener視点**で、kabu-signal・Kabu Noteとの連携を整理した
Phase 3統合の元資料です。同種のファイルが`kabu-signal/docs/INTEGRATION_NOTES.md`
（kabu-signal視点）・`Kabu-Note/docs/INTEGRATION_NOTES.md`（Kabu Note視点）にも存在します。
3ファイルは記述内容が一部重複しますが、**本ファイルは実際のコード・実際のHTTPレスポンスを
2026-09-02時点で直接検証した内容**であり、他2ファイル（同日付だが記述に古い情報や誤りが
一部残っている）との相違点は明記しています。

前提として本サービス側の全体像は [`docs/PROJECT_STATE.md`](PROJECT_STATE.md) を参照。

---

## 0. 最初に読むべき重大事項（3アプリ統合前に必ず対処すべき問題）

Phase 3着手前に、以下は**放置すると統合作業の土台が崩れる**レベルの問題として先に共有します。

### 0-1. 🔴 Kabu Noteの screener 連携が本番で壊れている（CORS）

`Kabu-Note/src/hooks/useScreenerData.js`は
`https://nobinobi9000.github.io/japan-stock-screener/latest.json`を直接`fetch()`しているが、
実際にこのURLへアクセスすると **`screener.nobi-labo.com`へ301リダイレクトされ、
そのリダイレクトレスポンスにCORSヘッダが一切無い**ため、ブラウザからの`fetch()`は失敗する。
2026-09-02に`curl`で実測確認済み:

```
$ curl -sI https://nobinobi9000.github.io/japan-stock-screener/latest.json
HTTP/1.1 301 Moved Permanently
Location: http://screener.nobi-labo.com/latest.json
（Access-Control-Allow-Origin ヘッダなし）
```

さらに、リダイレクト先の`screener.nobi-labo.com`は現在GitHub Pagesではなく
**Vercel（`japan-stock-screener/webapp/`）を指しており**、`/latest.json`というパスは
Next.js側に存在しないため`proxy.ts`のミドルウェアに捕まって`/login`へ307される
（`docs/PROJECT_STATE.md` 6節参照）。

**影響**: `Kabu-Note/src/components/ScreenerWidget.jsx`（ダッシュボードの「今日のピックアップ」）と
`Kabu-Note/src/pages/Market.jsx`（市場マップ）は、**本番で常にfetch失敗し、
古いlocalStorageキャッシュ表示 or エラー表示のまま**になっている可能性が高い
（初回訪問者はキャッシュも無いためエラー表示になる）。

**推奨する直し方（Kabu Note側の1行修正、japan-stock-screener側の変更は不要）**:
`SCREENER_URL`を`raw.githubusercontent.com`経由に変更する。webappの
`webapp/app/api/free-latest/route.ts`が既に同じ理由でこの経路を採用しており、
CORSヘッダも確認済み（2026-09-02 curl確認: `Access-Control-Allow-Origin: *`）。

```diff
- const SCREENER_URL = 'https://nobinobi9000.github.io/japan-stock-screener/latest.json'
+ const SCREENER_URL = 'https://raw.githubusercontent.com/nobinobi9000/japan-stock-screener/main/docs/latest.json'
```

または、webapp自体が持つ`https://screener.nobi-labo.com/api/free-latest`
（サーバー側プロキシ・キャッシュ付き）を叩く方式に統一するほうが将来性は高い（3-1節）。

> この修正はKabu Note側リポジトリで行うものであり、本ドキュメント作成セッションでは
> **まだ実施していません**。ユーザーへの報告時に対応要否を確認すること。

### 0-2. `docs/CNAME`が実態と合っていない

`docs/CNAME`には`screener.nobi-labo.com`と書かれているが、実際のDNSは
GitHub PagesではなくVercelを指している（0-1節参照）。GitHub Pages機能自体は
`nobinobi9000.github.io/japan-stock-screener/`という素のURLでは生きているため、
`docs/latest.json`は**そちらのURLでは**正常に配信され続けている
（CORSヘッダも本来は問題なし、301を挟まなければ）。

### 0-3. 姉妹ドキュメントの相互不整合

- `kabu-signal/docs/INTEGRATION_NOTES.md`は screener バッチの実行時刻を
  「16:07 JST」と記載しているが、これは**2026-08-29以前の値**。
  2026-08-27〜28にGitHub純正cronが最大14時間遅延・完全未発火する障害が発生したため、
  現在は`cloudflare-watchdog/`という外部Workerが**16:30 JSTに1回目、
  未成功なら18:30 JSTに2回目**という形でscreenerを起動している
  （`docs/PROJECT_STATE.md` 6節1項、8-3節）。実測（2026-08-31・09-01）でも
  `07:30:5x UTC`＝16:30 JST起動を確認済み。kabu-signal側の21:00 JST実行との
  バッファは「4時間53分」ではなく実質「4時間30分」に縮まっている点は、
  致命的ではないが認識しておくこと。
- `Kabu-Note/docs/PROJECT_STATE.md` 5-4節は「kabu-signalとの連携: 現状は直接の連携なし」と
  記載しているが、これは誤り。kabu-signalの`screener/user_matcher.py`が
  Kabu Noteの`watchlist`/`holdings`テーブルを**service_roleキーで直接読んでいる**
  （Kabu Note側のアプリケーションコードを一切経由しない、Supabase上でのサーバー間連携）。
  Kabu Note側からは見えない経路のため、この記述ミスは起きやすい。1-3節で詳述。

### 0-4. 🔴 `screener_stock_snapshots`の欠落は「修正済み」ではなく未解決（2026-09-02 Supabase実データで検証）

commit `2ccb14d`（numpy.bool_/float64 JSONシリアライズ修正、`git log`で確認した正確な日付は
**2026-08-22 21:36:39 +0900**）は、当初「これで解消」と見なされていたが、Supabaseへ直接
SELECTした結果、**修正後も間欠的に再発し続けている**ことを確認した。

| snapshot_date | `screener_snapshots`（メタ、is_incomplete） | `screener_stock_snapshots`（銘柄別） |
|---|---|---|
| 2026-08-24〜26 | false（正常） | 正常（各4,439行） |
| **2026-08-27** | false（正常） | **0行** |
| **2026-08-28** | false（正常） | **0行** |
| 2026-08-31 | false（正常） | 正常（4,439行） |
| **2026-09-01** | false（正常） | **0行** |

`export_snapshot_to_supabase()`（`stock_screener_v3_multiplan.py:3233`）はメタ行の書き込みと
銘柄別500件バッチ送信が別処理で、後者は例外を握りつぶすtry/exceptに包まれているため、
**メタ行が`is_incomplete=false`で正常に見えても銘柄別データだけ全滅する日がある**。
kabu-signalの鮮度ガードはメタ行の`is_incomplete`しか見ないため、この欠落を検知できない。
原因は未特定（Aug22の修正だけでは8/27・8/28・9/1の再発を説明できない）。
詳細・改修方針は`docs/PROJECT_STATE.md` 6節9項を参照。

---

## 1. 現在共有しているデータ・ファイル・API・DBテーブル

japan-stock-screenerは、他2サービスに対して**一方的にデータを提供する側**であり、
kabu-signal・Kabu Noteのデータを読み取ることは一切ない（原則2の帰結）。

### 1-1. `docs/latest.json` → Kabu Note（現状は経路が壊れている、0-1節）

| 項目 | 内容 |
|---|---|
| 生成元 | `stock_screener_v3_multiplan.py` の `export_json()`（2570行目） |
| ファイル | `japan-stock-screener/docs/latest.json` |
| 本来の意図した公開先 | GitHub Pages（`docs/CNAME`は`screener.nobi-labo.com`を指しているが0-2節の通り実態と不一致） |
| 実際に生きているURL | `https://nobinobi9000.github.io/japan-stock-screener/latest.json`（素のGitHub Pages URL） |
| 読み手 | Kabu Note `src/hooks/useScreenerData.js`（現状CORSで失敗、0-1節） |
| 内容 | `date` / `top3`（厳選3銘柄） / `sector_heatmap`（業種別平均スコア） / `market_summary` |
| 更新頻度 | 平日16:30〜16:50 JST頃（`cloudflare-watchdog`起動→バッチ完了まで） |

**同じファイルをwebapp自身も読んでいる**（`webapp/lib/useScreenerData.ts` →
`webapp/app/api/free-latest/route.ts`経由。こちらは`raw.githubusercontent.com`直叩きの
サーバー側プロキシなのでCORS問題なし）。つまり現状、**同じ`docs/latest.json`を
「壊れた経路のKabu Note」と「正常な経路のwebapp自身」の2通りの方法で配信している**。

### 1-2. Supabase `screener_snapshots` / `screener_stock_snapshots` → kabu-signal

| 項目 | 内容 |
|---|---|
| 書き込み元 | `export_snapshot_to_supabase()`（`stock_screener_v3_multiplan.py:3233`） |
| 読み手 | kabu-signal `screener/jvqm_screener.py` の `fetch_latest_snapshot()` / `wait_for_fresh_snapshot()` |
| 認証方式 | 双方とも`SUPABASE_SERVICE_ROLE_KEY`（RLSを越える管理者権限、GitHub Secretsとして各リポジトリが個別に保持） |
| Supabaseプロジェクト | `nhkgyipjeithytqqfuda`（**Kabu Note・kabu-signal・screener/webappの3者が完全に同じプロジェクトを共有**していることを2026-09-02に3リポジトリの`.env.local`で実値照合済み） |
| kabu-signalが実際に参照するクエリ | `GET /rest/v1/screener_snapshots?select=*&order=snapshot_date.desc&limit=1`<br>`GET /rest/v1/screener_stock_snapshots?select=*&snapshot_date=eq.{date}&fetch_success=eq.true` |
| kabu-signalが使うカラム | `snapshot_date`, `is_incomplete`, `success_rate`（鮮度判定）／ `code`, `name`, `close_price`, `jvqm_pbr`, `jvqm_roe`, `jvqm_fcf_yield`, `jvqm_beta`, `jvqm_dividend_yield`, `jvqm_score`, `momentum_12m`, `near_52w_high`, `dead_cross`, `ma200_breakdown`, `ichimoku_bearish`, `bb_lower_break`, `obv_downtrend`, `volume_surge_down`, `fetch_success`（データ本体） |
| 鮮度ガード | kabu-signal側で「今日の日付か」「`is_incomplete=false`か」を確認し、不合格なら15分間隔・最大3回リトライ（`wait_for_fresh_snapshot(max_retries=3, retry_interval_sec=900)`）。全滅した場合は「本日配信なし」をユーザーへ通知（原則5） |

`account_entitlements`/`account_external_identities`（webappがStripe連携用に書き込む
テーブル、`docs/PROJECT_STATE.md` 4-2節）は同じSupabaseプロジェクト内にあるが、
kabu-signal・Kabu Noteがこれを参照しているコードは本ドキュメント作成時点で確認できていない
（Kabu Note自身は独自の`account_entitlements`行を持っており、webapp発行分とは別ユーザー基盤
として扱われている可能性がある。3-4節で詳述）。

### 1-3. screenerは経由しないが、事実として存在する連携（参考情報）

japan-stock-screener自身の連携ではないが、**同じSupabaseプロジェクトを共有しているために
起きている**連携としてkabu-signalが以下も直接読んでいる。screenerのDBスキーマ変更判断に
影響するため記録しておく。

| テーブル | 書き込み | 読み取り | 用途 |
|---|---|---|---|
| `watchlist`（Kabu Note所有） | Kabu Noteユーザー操作 | kabu-signal `user_matcher.py`（`select=user_id,code`） | 買いシグナル突合 |
| `holdings`（Kabu Note所有） | Kabu Noteユーザー操作 | kabu-signal `user_matcher.py`（`select=user_id,code`／`select=user_id,code,cost_price`） | 売りシグナル突合・損益アラート |
| `pnl_alert_settings`（kabu-signal所有、Kabu Note側UIは未実装） | （未実装） | kabu-signal `user_matcher.py` | 損益アラート閾値 |

japan-stock-screenerはこれら3テーブルを一切参照しない。

### 1-4. screenerが「例外的に許可された」独自取得（原則2の例外）

CLAUDE.mdの原則2は「signalの独自取得はTDnet適時開示のみ許可」としているが、
**kabu-signalの実装は現在TDnetではなくkabutan.jp（`https://kabutan.jp/warning/`）を
スクレイピングしている**（`kabu-signal/screener/tdnet_checker.py`のdocstring: 「TDnetの
URLが無効になったためkabutan.jpのwarningページに置き換え」）。kabutan.jpはTDnet開示情報を
集約表示するサイトであり原則の趣旨は保たれているが、**原則の文言とコードの実体が一致していない**
点は、CLAUDE.mdを更新するか実装をTDnet直接取得に戻すか、いずれかの整理が必要。

---

## 2. データの受け渡しの方向とタイミング

2026-09-02時点で実測・コード確認した実際のタイムライン（JST）:

```
平日
─────────────────────────────────────────────────────────────
16:30   cloudflare-watchdog が japan-stock-screener を workflow_dispatch で起動（1回目）
        ├─ shard-screen ×10（並列、yfinance取得＋9指標判定）
        └─ aggregate-screen
            ├─ Supabase: screener_snapshots に UPSERT
            ├─ Supabase: screener_stock_snapshots に UPSERT（全銘柄）
            └─ GitHub Pages: docs/latest.json を commit & push
        （所要時間の実績: 17〜30分。16:47〜17:00頃に完了）

16:xx   Kabu Note の update_stocks.py が実行（GitHub Actions、平日16時JST、screenerとは独立）
        └─ Supabase: stocks / daily_history / dividend_records を更新
        ※ screenerの完了を待たない。これはKabu Note独自のyfinance取得であり、
          screenerのデータとは無関係（保有銘柄の株価表示用）

18:30   cloudflare-watchdog: 16:30時点で未成功なら screener を再起動（2回目）

20:00   cloudflare-watchdog: それでも未成功ならResend経由で管理者にメールアラート
        （kabu-signalの鮮度ガードはこの状態でも21:00に動き出し、最終的に
          「本日配信なし」を利用者に通知する形で自己防衛する）

21:00   kabu-signal バッチ実行（screenerの1回目起動から4時間30分後）
        ├─ jvqm_screener.py: screener_snapshots で鮮度確認 → 不合格なら15分×3回リトライ
        ├─ tdnet_checker.py: kabutan.jpから当日の適時開示を取得（原則2の例外）
        ├─ user_matcher.py: Kabu Noteの watchlist/holdings を参照して個別突合
        ├─ push_sender.py: /api/push/send（kabu-signal.vercel.app）へPOST
        └─ signals/latest.json を commit & push
─────────────────────────────────────────────────────────────

Kabu Note フロントエンド（ユーザーがアプリを開いた時点、時刻不定）
  └─ useScreenerData.js が docs/latest.json をfetch（0-1節: 現状失敗する）
      └─ 当日分がlocalStorageにキャッシュ済みならスキップ（1日1回）
```

**順序に関する制約**: screener（16:30起動）→ kabu-signal（21:00起動）の順序が
入れ替わってはならない。kabu-signalの鮮度ガードは「今日の日付のスナップショットか」を
見るだけで「screenerが今日ちゃんと完了したか」を積極的に待つわけではないため、
screener側の起動が21:00より後にずれ込むと、kabu-signalは前日データで走るか、
鮮度ガード不合格で配信を見送ることになる。

---

## 3. 現状は連携していないが、将来連携させたい／させる可能性がある箇所

### 3-1. 配信経路をSupabase（またはwebapp API）に一本化する（優先度: 高）

**現状の問題**: screenerは「GitHub Pages経由のdocs/latest.json」と「Supabase経由の
全銘柄スナップショット」という**2つの別々の配信経路**を持っており、GitHub Pages側は
0-1/0-2節の通りDNS変更で実質機能不全に陥っている。

**将来案**: `docs/latest.json`の配信を廃止し、Kabu Noteも
`https://screener.nobi-labo.com/api/free-latest`（webappが既に持つエンドポイント、
サーバー側プロキシなのでCORS安全・キャッシュ付き）を叩く方式に統一する。
これにより：
- GitHub Pagesという配信経路自体が不要になり、`docs/CNAME`・`docs/index.html`の
  メンテナンス負債も解消できる
- 原則3（有料コンテンツを公開経路に置かない）の観点でも、無料枠の配信元を
  webapp側のアクセス制御下に統一でき、将来の認証強化がしやすくなる
- ただしKabu Note側の改修（fetch先URL変更）は必須。webapp側は変更不要

### 3-2. Kabu Note保有銘柄をscreenerの取得対象に統合する（優先度: 中）

現在Kabu Noteの`update_stocks.py`は、`holdings`テーブルにある銘柄だけを対象に
**独自にyfinanceを呼んでいる**（原則2で明示的に許可された唯一の例外）。screenerは
東証全銘柄を毎日スキャンしているため理論上はデータが重複しているが、
screenerの`screener_stock_snapshots`には保有単価等のユーザー個別情報が無く、
Kabu Note側のニーズ（保有株数×現在値の評価額計算、配当情報等）を満たすには
screener側のスキーマ拡張が必要。**すぐには実現しない**が、統合すればyfinance呼び出し
経路が実質1つになり原則2がより厳密に守られる。

### 3-3. Supabase Auth共有をscreener webapp側でも活かす（優先度: 中、一部は現在進行形）

`japan-stock-screener/webapp`は既にKabu Note・kabu-signalと**同一のSupabase Authプロジェクト**
でログイン機能を実装済み（ログインページの文言にも「Kabu Note・kabu-signalと共通のアカウントで
ログインできます」と明記）。ただし3サービスはそれぞれ別ドメイン
（screener.nobi-labo.com / kabu.nobi-labo.com / signal.nobi-labo.com、
後2者は本ドキュメント作成セッションでは実ドメインを直接確認していない）のため、
**ブラウザのセッションCookieは共有されず、サービスをまたぐたびに再ログインが必要**。
将来的にサブドメインを揃える・SSO的な仕組みを入れる、という改善余地がある
（kabu-signal側のINTEGRATION_NOTES.mdにも同様の指摘あり）。

### 3-4. cloudflare-watchdogパターンのkabu-signalへの展開（優先度: 中、screener発の技術資産）

kabu-signalの`morning-scan.yml`は現在もGitHub純正の`schedule:`トリガー
（`cron: '0 12 * * 1-5'`）に依存しており、screenerが2026-08-27に経験したのと
**全く同じ「最大数時間〜終日の遅延・未発火」リスク**を抱えている。screenerで構築した
`cloudflare-watchdog/`（外部トリガー＋リトライ＋メールアラート）の設計はそのまま
kabu-signal側にも移植可能。これはscreener側の変更ではなくkabu-signal側の対応事項だが、
実装パターンを再利用できる資産として記録しておく。

### 3-5. `account_entitlements`のプラン判定を3サービスで統一する（優先度: 低〜中、要調査）

webapp（screener）・Kabu Noteはそれぞれ`account_entitlements`テーブルの`plan`列
（free/basic/premium）でプラン判定しているが、**同じテーブル・同じidを見ているのか、
それぞれ別レコードを持っているのかは本ドキュメント作成時点で未検証**。
Stripeの決済主体がwebapp（screener）側の`STRIPE_BASIC_PRICE_ID`のみである以上、
Kabu Note・kabu-signal側で「有料」と判定されるユーザーが今どう決まっているのかは
Phase 3で必ず確認・整理が必要な論点。

---

## 4. 連携関連の処理を変更した場合に他の2つのアプリへ影響が出る条件

### 4-1. `screener_stock_snapshots` / `screener_snapshots`（Supabase）を変更する場合

- **カラムの追加**: 安全。kabu-signalの`jvqm_screener.py`は`select=*`で全カラム取得するため
  追加分は単に無視される
- **カラムの削除・リネーム**: kabu-signalが読んでいる以下のカラムは変更禁止、または
  変更時は`kabu-signal/screener/jvqm_screener.py`の`fetch_latest_snapshot()`と
  `run()`内のフィールド参照を同時に修正すること:
  `snapshot_date`, `is_incomplete`, `success_rate`, `code`, `name`, `close_price`,
  `jvqm_pbr`, `jvqm_roe`, `jvqm_fcf_yield`, `jvqm_beta`, `jvqm_dividend_yield`,
  `jvqm_score`, `momentum_12m`, `near_52w_high`, `dead_cross`, `ma200_breakdown`,
  `ichimoku_bearish`, `bb_lower_break`, `obv_downtrend`, `volume_surge_down`,
  `fetch_success`
- **`fetch_success`列のクエリ条件変更**: kabu-signalは`?fetch_success=eq.true`で
  絞り込んでいる。この挙動を変える場合はkabu-signal側のクエリも要修正
- **`is_incomplete`のロジック変更（`SNAPSHOT_INCOMPLETE_THRESHOLD`等）**: kabu-signalの
  鮮度ガードが「不完全」と判定する基準がずれる。両者で閾値の意味を揃えること

### 4-2. `docs/latest.json`のスキーマを変更する場合

- Kabu Note: `useScreenerData.js`は`data.top3`/`data.sector_heatmap`を、
  `ScreenerWidget.jsx`は`stock.code/name/score/risk_tag/sector`を、
  `Market.jsx`は`s.name/avg_score/stock_count`を参照。キー変更は全て要追随修正
  （ただし0-1節の通り現状この経路自体が壊れているため、実害は限定的）
- webapp: `webapp/lib/useScreenerData.ts`が同じ`top3`/`sector_heatmap`/`market_summary`を
  参照。こちらは実際に本番で機能しているため、変更時は必ずwebapp側も同時に確認すること

### 4-3. バッチ実行時刻（cloudflare-watchdog）を変更する場合

- kabu-signalの実行時刻（21:00 JST）より**必ず前**に完了させること。目安として
  1回目起動から遅くとも3〜4時間以内には完了させる余裕を残す（現状の所要時間実績は
  17〜30分なので、20:00の最終アラート時刻を後ろにずらす分には比較的余裕がある）
- 変更する場合、kabu-signal側の`.github/workflows/morning-scan.yml`のコメント
  （「Phase 5 項目2で7:00→21:00に変更」等、screenerの時刻を前提にした記述）も
  合わせて更新が必要になる可能性がある

### 4-4. Supabaseプロジェクトを移行・分離する場合

- 3サービス（screener/webapp・kabu-signal・Kabu Note）すべてが同一プロジェクト
  （`nhkgyipjeithytqqfuda`）の`NEXT_PUBLIC_SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY`を
  使っている。screener側だけを別プロジェクトに切り出すと、kabu-signalの
  `screener_snapshots`/`screener_stock_snapshots`読み取りが即座に全滅する
- GitHub Secrets（screener・kabu-signal双方）とVercel環境変数（webapp）を
  同時に更新する必要がある

### 4-5. `screener_stock_snapshots`のRLSポリシーを変更する場合

- kabu-signalはservice_roleキーで読んでいるため、通常のRLS変更（authenticated/anon向け）は
  影響しない。ただし**service_role自体のアクセスを制限する設定**を誤って入れると
  kabu-signalが全銘柄データを読めなくなり、シグナル0件のまま沈黙する
  （鮮度ガードで検知され「配信なし」通知にはなるが、原因究明が難しくなる）

### 4-6. GitHub Pagesのカスタムドメイン（`docs/CNAME`）を変更・削除する場合

- 現状`screener.nobi-labo.com`は実質Vercel（webapp）が使っているドメインなので、
  `docs/CNAME`を削除してもwebapp側への影響は無い
- 一方、`docs/CNAME`を削除すると`https://nobinobi9000.github.io/japan-stock-screener/*`への
  301リダイレクトも解消される可能性があり、**むしろKabu Noteの現行コード
  （0-1節、修正前の状態）がそのまま動くようになる**副次効果がある。ただし
  3-1節の統一方針を採るなら、この暫定対応より恒久対応（Kabu Note側のURL変更）を優先すべき

---

## 5. 未検証・要調査として残した項目（Phase 3着手前に埋めること）

- kabu-signal・Kabu Noteの本番ドメイン（`signal.nobi-labo.com`・`kabu.nobi-labo.com`と
  推定されるが、本ドキュメント作成セッションでは`kabu.nobi-labo.com`のみ実地確認）のDNS/デプロイ先
- `account_entitlements`が3サービスで本当に同一レコードを指しているか（3-5節）
- webappの`/api/free-latest`・`/api/snapshot`に対する、Kabu Note・kabu-signalからの
  実際の利用実績（現状は「webapp自身が自分のために使っている」ことしか確認できていない）
- ~~`screener_stock_snapshots`の欠落が正常化しているかの継続監視~~ →
  **検証済み・未解決（0-4節参照）**。「次回バッチで解消見込み」ではなく、
  `export_snapshot_to_supabase()`の銘柄別バッチ送信部分に失敗原因を可視化する
  改修が必要な状態

---

*このファイルを更新した場合は末尾の「最終更新」日付を変えること。*
