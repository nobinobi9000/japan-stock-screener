// my-invest tick のテスト（C19〜C22）。fetch はモック。時刻は event.scheduledTime で注入する。
// このリポジトリは PUBLIC のため、値はすべて架空。
import test, { mock } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  ENV, KN_CRON, KN_RUNS_RE, KN_DISPATCH_RE, SCREENER_RUNS_RE, SCREENER_JOBS_RE,
  jstMs, run as baseRun, invoke, posts,
} from "./helpers.js";

const D = "2026-11-18";
// 起動先の run-name が display_title に入れる値。このファイルの run は既定で実運用(dry_run=false)。
const LIVE_TITLE = "weekday check (dry_run=false)";
const DRY_TITLE = "weekday check (dry_run=true)";
const run = (...args) => ({ ...baseRun(...args), display_title: LIVE_TITLE });
const titled = (r, title) => ({ ...r, display_title: title });
const dryRun = (...args) => titled(baseRun(...args), DRY_TITLE);
const MI_ENV = {
  MY_INVEST_REPO: "invest-repo",
  MY_INVEST_WORKFLOW_FILE: "weekday.yml",
  MY_INVEST_GITHUB_TOKEN: "dummy-invest-token",
  MY_INVEST_DRY_RUN: "false",
};
const MI_RUNS_RE = /\/repos\/test-owner\/invest-repo\/actions\/workflows\/weekday\.yml\/runs/;
const MI_DISPATCH_RE = /\/repos\/test-owner\/invest-repo\/actions\/workflows\/weekday\.yml\/dispatches/;

/** invest: runs配列 | {error:500}。kabu・screener は他経路の独立性確認用 */
function scenario({ invest = [], kabu = [], screener = [] }) {
  return (url, call) => {
    if (MI_RUNS_RE.test(url) && call.method === "GET") {
      if (invest && invest.error) return { status: invest.error, body: "err" };
      return { body: { workflow_runs: invest } };
    }
    if (MI_DISPATCH_RE.test(url) && call.method === "POST") return { status: 204, body: "" };
    if (KN_RUNS_RE.test(url) && call.method === "GET") return { body: { workflow_runs: kabu } };
    if (KN_DISPATCH_RE.test(url) && call.method === "POST") return { status: 204, body: "" };
    if (SCREENER_RUNS_RE.test(url)) return { body: { workflow_runs: screener } };
    if (SCREENER_JOBS_RE.test(url)) return { body: { jobs: [{ name: "aggregate-screen", conclusion: "success" }] } };
    if (/api\.resend\.com\/emails/.test(url) && call.method === "POST") return { body: { id: "x" } };
    return null;
  };
}

const isDispatch = (c) => MI_DISPATCH_RE.test(c.url);
const isMail = (c) => /resend/.test(c.url);
const miCalls = (calls) => calls.filter((c) => /invest-repo/.test(c.url));

async function tick(hhmm, sc, { date = D, env = {} } = {}) {
  return invoke({ cron: KN_CRON, scheduledTime: jstMs(date, hhmm), env: { ...MI_ENV, ...env }, handler: scenario(sc) });
}

function classify(calls) {
  const p = posts(calls);
  if (p.some(isDispatch)) return "dispatch";
  if (p.some(isMail)) return "mail";
  return "none";
}

const ok = (end = "17:40") => run(1, D, "17:30", end, "completed", "success");
const fail = (id, s, e, concl = "failure") => run(id, D, s, e, "completed", concl);

// [#, 時刻, シナリオ, 期待: "none"|"dispatch"|"mail"]
const TABLE = [
  [1, "17:25", { invest: [] }, "none"],
  [2, "17:30", { invest: [] }, "dispatch"],
  [3, "17:30", { invest: [run(1, D, "17:30", "17:31", "in_progress", null)] }, "none"],
  [4, "17:35", { invest: [run(1, D, "17:30", "17:31", "queued", null)] }, "none"],
  [5, "17:45", { invest: [ok()] }, "none"],
  [6, "17:55", { invest: [fail(1, "17:30", "17:40")] }, "none"],
  [7, "18:05", { invest: [fail(1, "17:30", "17:40")] }, "none"],
  [8, "18:10", { invest: [fail(1, "17:30", "17:40")] }, "dispatch"],
  [9, "18:15", { invest: [fail(1, "17:30", "17:40")] }, "dispatch"],
  [10, "19:00", { invest: [fail(1, "17:30", "17:40"), fail(2, "18:10", "18:20"), fail(3, "18:50", "18:55", "timed_out")] }, "none"],
  [11, "19:25", { invest: [] }, "dispatch"],
  [12, "19:30", { invest: [] }, "none"],
  [13, "17:40", { invest: [run(9, D, "17:30", "17:35", "completed", "cancelled")] }, "dispatch"],
  [14, "17:40", { invest: [run(9, "2026-11-17", "17:30", "17:35", "completed", "success")] }, "dispatch"], // 前日の成功は数えない
  [15, "17:40", { invest: [run(9, D, "17:00", "17:05", "completed", "success", "schedule")] }, "dispatch"], // schedule は数えない
  [16, "18:30", { invest: [ok("17:40"), fail(2, "18:00", "18:10")] }, "none"], // 成功が1回でもあれば再起動しない（冪等）
  [17, "20:05", { invest: [] }, "none"],
  [18, "20:10", { invest: [] }, "mail"],
  [18.1, "20:10", { invest: [fail(1, "17:30", "17:40")] }, "mail"],
  [18.2, "20:10", { invest: [run(1, D, "19:50", "20:00", "in_progress", null)] }, "mail"],
  [19, "20:10", { invest: [ok()] }, "none"],
  [20, "20:10", { invest: { error: 500 } }, "mail"],
  [21, "20:15", { invest: [] }, "none"],
  [22, "03:00", { invest: [] }, "none"],
];

test("C20 起動時刻の表", async () => {
  for (const [n, hhmm, sc, expected] of TABLE) {
    const r = await tick(hhmm, sc);
    assert.equal(classify(r.calls), expected, `#${n} ${hhmm}`);
    if (expected === "dispatch" || expected === "mail") assert.equal(posts(r.calls).length, 1, `#${n}`);
    if (expected === "dispatch") {
      const body = posts(r.calls)[0].body;
      assert.equal(body.ref, "main");
      assert.deepEqual(body.inputs, { dry_run: "false" }, `#${n}`);
    }
  }
});

test("C20 窓の外は my-invest 向け API 呼び出し 0 回", async () => {
  for (const hhmm of ["17:25", "19:30", "20:05", "20:15", "21:00", "03:00", "16:00"]) {
    const r = await tick(hhmm, { invest: [] });
    assert.equal(miCalls(r.calls).length, 0, hhmm);
  }
});

test("C20 確認不能メールの文面", async () => {
  const r = await tick("20:10", { invest: { error: 500 } });
  assert.match(posts(r.calls)[0].body.text, /確認できませんでした/);
});

test("C20 run 取得 URL に event=workflow_dispatch が含まれる", async () => {
  const r = await tick("17:30", { invest: [] });
  const g = r.calls.filter((c) => MI_RUNS_RE.test(c.url));
  assert.equal(g.length, 1);
  assert.match(g[0].url, /event=workflow_dispatch/);
});

test("C20 JST の日付・時刻だけで決まる（UTC日付が違う・月末・年末年始・曜日違い）", async () => {
  // 2026-11-18T15:30Z = JST 11/19 00:30 は窓の外
  const r0 = await invoke({
    cron: KN_CRON, scheduledTime: Date.parse("2026-11-18T15:30:00Z"), env: MI_ENV, handler: scenario({ invest: [] }),
  });
  assert.equal(miCalls(r0.calls).length, 0);
  // 2026-11-19T08:30Z = JST 11/19 17:30（UTC と JST が同日）。2026-11-19T09:00Z = JST 18:00
  const r1 = await invoke({
    cron: KN_CRON, scheduledTime: Date.parse("2026-11-19T08:30:00Z"), env: MI_ENV, handler: scenario({ invest: [] }),
  });
  assert.equal(classify(r1.calls), "dispatch");

  const dates = ["2026-11-16", "2026-11-18", "2026-11-21", "2026-11-23", "2026-11-30", "2026-12-31", "2027-01-01", "2027-01-04"];
  for (const date of dates) {
    const okRun = run(1, date, "17:30", "17:40", "completed", "success");
    const r = await tick("17:30", { invest: [] }, { date });
    assert.equal(classify(r.calls), "dispatch", date);
    assert.deepEqual(posts(r.calls)[0].body.inputs, { dry_run: "false" });
    const rs = await tick("17:45", { invest: [okRun] }, { date });
    assert.equal(classify(rs.calls), "none", date);
    const rm = await tick("20:10", { invest: [] }, { date });
    assert.equal(classify(rm.calls), "mail", date);
    assert.match(posts(rm.calls)[0].body.subject, new RegExp(date));
    // 前日の run しか無ければ今日分とは見なさない
    const prev = run(2, "2026-01-01", "17:30", "17:40", "completed", "success");
    const ry = await tick("17:30", { invest: [prev] }, { date });
    assert.equal(classify(ry.calls), "dispatch", date);
  }
  // 翌日 01:00(JST) 作成の run は、その前日(UTC 日付では同日)の分に数えない
  const late = run(3, "2026-11-19", "01:00", "01:05", "completed", "success");
  const r2 = await tick("17:30", { invest: [late] }, { date: D });
  assert.equal(classify(r2.calls), "dispatch");
});

test("C21 my-invest.js は new Date( / Date.now( を使わない", () => {
  const src = readFileSync(new URL("../src/my-invest.js", import.meta.url), "utf8");
  assert.equal(/new Date\(/.test(src), false);
  assert.equal(/Date\.now\(/.test(src), false);
});

test("C22 DRY モードは GET のみ（既定・未設定・不正値）", async () => {
  for (const [n, hhmm, sc] of TABLE) {
    const r = await tick(hhmm, sc, { env: { MY_INVEST_DRY_RUN: "true" } });
    assert.equal(posts(r.calls).length, 0, `#${n}`);
    assert.equal(r.calls.filter(isMail).length, 0, `#${n}`);
  }
  const r = await tick("17:30", { invest: [] }, { env: { MY_INVEST_DRY_RUN: "true" } });
  assert.ok(r.logs.some((l) => /\[DRY\].*起動する予定/.test(l)));
  assert.equal(miCalls(r.calls).length, 1); // GET 1回のみ
  const m = await tick("20:10", { invest: [] }, { env: { MY_INVEST_DRY_RUN: "true" } });
  assert.ok(m.logs.some((l) => /\[DRY\].*メールを送る予定/.test(l)));
  for (const v of [undefined, "", "TRUE", "0", "no", "False1"]) {
    for (const [hhmm, sc] of [["17:30", { invest: [] }], ["20:10", { invest: [] }]]) {
      const rr = await invoke({
        cron: KN_CRON, scheduledTime: jstMs(D, hhmm),
        env: v === undefined ? { ...MI_ENV, MY_INVEST_DRY_RUN: undefined } : { ...MI_ENV, MY_INVEST_DRY_RUN: v },
        handler: scenario(sc),
      });
      assert.equal(posts(rr.calls).filter((c) => isDispatch(c) || /invest/.test(c.url)).length, 0, `dry=${v} ${hhmm}`);
      assert.equal(rr.calls.filter(isMail).length, 0, `dry=${v} ${hhmm}`);
    }
  }
  const live = await tick("17:30", { invest: [] }, { env: { MY_INVEST_DRY_RUN: "false" } });
  assert.equal(posts(live.calls).filter(isDispatch).length, 1);
});

test("C22 DISPATCH 段階の API エラー: POST 0 回・エラーがログに残り、例外は伝播しない", async () => {
  const r = await tick("17:30", { invest: { error: 500 } });
  assert.equal(posts(r.calls).length, 0);
  assert.ok(r.errors.some((e) => /DISPATCH段階でエラー/.test(e)));
  assert.equal(r.pending.length, 1);
});

test("C22 fetch が例外を投げても scheduled() は例外を出さない", async () => {
  const r = await invoke({
    cron: KN_CRON, scheduledTime: jstMs(D, "17:30"), env: MI_ENV,
    handler: () => { throw new Error("network down"); },
  });
  assert.equal(posts(r.calls).length, 0);
  assert.ok(r.errors.length >= 1);
});

test("C22 dispatch が 422 のときは入力なしで再送しない", async () => {
  const handler = (url, call) => {
    if (MI_DISPATCH_RE.test(url)) return { status: 422, body: "Unexpected inputs" };
    return scenario({ invest: [] })(url, call);
  };
  const r = await invoke({ cron: KN_CRON, scheduledTime: jstMs(D, "17:30"), env: MI_ENV, handler });
  assert.equal(posts(r.calls).length, 1);
  assert.ok(r.errors.some((e) => /workflow_dispatch失敗: 422/.test(e)));
});

test("C22 トークン未設定: GITHUB_TOKEN へフォールバックせず、API 0 回・POST 0 回・エラーがログに残る", async () => {
  for (const tok of [undefined, ""]) {
    for (const hhmm of ["17:30", "20:10"]) {
      const r = await invoke({
        cron: KN_CRON, scheduledTime: jstMs(D, hhmm),
        env: { ...MI_ENV, MY_INVEST_GITHUB_TOKEN: tok }, // ENV.GITHUB_TOKEN は設定済み
        handler: scenario({ invest: [] }),
      });
      assert.equal(miCalls(r.calls).length, 0, hhmm);
      assert.equal(posts(r.calls).filter((c) => isDispatch(c) || isMail(c)).length, 0, hhmm);
      assert.equal(r.calls.some((c) => String(c.headers && c.headers.Authorization).includes("undefined")), false);
      assert.ok(r.errors.some((l) => /トークン未設定/.test(l)), hhmm);
    }
  }
});

test("C22 トークンは my-invest 向けにだけ使い、値はログ・メールに出ない", async () => {
  const r = await tick("17:30", { invest: [] });
  const auth = r.calls.filter((c) => /invest-repo/.test(c.url)).map((c) => c.headers.Authorization);
  assert.deepEqual([...new Set(auth)], ["Bearer dummy-invest-token"]);
  const failing = await tick("17:30", { invest: { error: 500 } });
  for (const l of [...failing.logs, ...failing.warns, ...failing.errors]) {
    assert.equal(l.includes("dummy-invest-token") || l.includes("dummy-screener-token"), false);
  }
  const mail = await tick("20:10", { invest: [] });
  const m = posts(mail.calls).find(isMail);
  assert.equal(JSON.stringify(m.body).includes("dummy-invest-token"), false);
});

const FORBIDDEN = ["推奨", "おすすめ", "エントリーに", "買い時", "売り時", "狙い目", "すべき", "勝率",
  "半分売る", "残りを売る", "買い候補", "損切り", "検討", "してください"];

test("C22 メールの安全性（日付・状態・URL のみ。禁止語・秘密様の値なし）", async () => {
  const states = [
    { invest: [] },
    { invest: [fail(1, "17:30", "17:40")] },
    { invest: [run(1, D, "19:50", "20:00", "in_progress", null)] },
    { invest: { error: 500 } },
  ];
  for (const sc of states) {
    const r = await tick("20:10", sc);
    const mail = posts(r.calls).find(isMail);
    assert.ok(mail);
    assert.equal(mail.body.to, ENV.ALERT_TO_EMAIL);
    assert.equal(mail.body.from, ENV.ALERT_FROM_EMAIL);
    const all = mail.body.subject + "\n" + mail.body.text;
    assert.match(all, new RegExp(D));
    assert.match(all, /https:\/\/github\.com\/test-owner\/invest-repo\/actions\/workflows\/weekday\.yml/);
    for (const bad of ["github_pat_", "ghp_", "re_", "eyJ", "dummy-"]) assert.equal(all.includes(bad), false, bad);
    for (const w of FORBIDDEN) assert.equal(all.includes(w), false, w);
  }
  // 20:10 以外の tick では送信 0
  for (const hhmm of ["17:30", "18:00", "19:25", "20:05", "20:15", "20:55"]) {
    const r = await tick(hhmm, { invest: [] });
    assert.equal(r.calls.filter(isMail).length, 0, hhmm);
  }
});

test("C22 ソースに禁止語が無い", () => {
  const src = readFileSync(new URL("../src/my-invest.js", import.meta.url), "utf8");
  for (const w of FORBIDDEN) assert.equal(src.includes(w), false, `my-invest.js: ${w}`);
});

test("scheduledTime が無い（debug fetch 経由）場合は何もしない", async () => {
  const r = await invoke({ cron: KN_CRON, scheduledTime: undefined, env: MI_ENV, handler: scenario({}) });
  assert.equal(r.calls.length, 0);
});

// ---- 手動 DRY 実行の除外（display_title）----

const drySuccess = (id = 50, s = "17:00", e = "17:05") => dryRun(id, D, s, e, "completed", "success");
const dryFail = (id, s, e) => dryRun(id, D, s, e, "completed", "failure");
// 表示名が欠損・想定外の run
const UNKNOWN_TITLES = [
  undefined, null, "", "my-invest weekday check", "weekday check (dry_run=)",
  "weekday check (dry_run=TRUE)", "weekday check (dry_run=falsex)",
];
const unknown = (title, id = 60, s = "17:30", e = "17:35", status = "completed", concl = "success") =>
  titled(baseRun(id, D, s, e, status, concl), title);

test("DRY除外: 手動DRYの成功があっても起動する（dry_run=false で POST 1回）", async () => {
  for (const hhmm of ["17:30", "18:00", "19:25"]) {
    const r = await tick(hhmm, { invest: [drySuccess()] });
    assert.equal(classify(r.calls), "dispatch", hhmm);
    assert.equal(posts(r.calls).length, 1, hhmm);
    assert.deepEqual(posts(r.calls)[0].body.inputs, { dry_run: "false" });
  }
});

test("DRY除外: dry_run=false の成功があれば、DRY の run が混在しても起動しない", async () => {
  for (const invest of [
    [ok()],
    [ok(), drySuccess()],
    [dryFail(51, "17:50", "17:55"), ok()],
    [dryRun(52, D, "17:44", "17:45", "in_progress", null), ok()],
  ]) {
    const r = await tick("17:55", { invest });
    assert.equal(posts(r.calls).length, 0);
    assert.ok(r.logs.some((l) => /成功済み/.test(l)));
  }
});

test("DRY除外: DRY の実行中・待機中は起動を止めない", async () => {
  for (const status of ["in_progress", "queued", "pending", "waiting"]) {
    const r = await tick("17:35", { invest: [dryRun(53, D, "17:30", "17:31", status, null)] });
    assert.equal(classify(r.calls), "dispatch", status);
  }
});

test("DRY除外: DRY の失敗は失敗回数・再試行の待ちに数えない", async () => {
  const three = [dryFail(1, "17:00", "17:05"), dryFail(2, "17:10", "17:15"), dryFail(3, "17:20", "17:25")];
  assert.equal(classify((await tick("17:30", { invest: three })).calls), "dispatch");
  // 直前に失敗した DRY があっても30分待たない
  const justNow = [dryFail(4, "17:50", "17:54"), dryRun(5, D, "17:40", "17:45", "completed", "timed_out")];
  assert.equal(classify((await tick("17:55", { invest: justNow })).calls), "dispatch");
  // 実運用の失敗2回 + DRY の失敗 は上限(3回)にならない
  const mixed = [fail(6, "17:30", "17:35"), fail(7, "18:10", "18:15"), dryFail(8, "18:20", "18:25")];
  assert.equal(classify((await tick("18:50", { invest: mixed })).calls), "dispatch");
});

test("判別不能: 成功は成功扱いにせず起動し、警告を残す", async () => {
  for (const title of UNKNOWN_TITLES) {
    const r = await tick("17:45", { invest: [unknown(title)] });
    assert.equal(classify(r.calls), "dispatch", String(title));
    assert.ok(r.warns.some((l) => /判別できない成功 run が1件/.test(l)), String(title));
  }
});

test("判別不能: 実運用の成功が別にあれば起動しない", async () => {
  const r = await tick("17:55", { invest: [unknown(undefined), ok()] });
  assert.equal(posts(r.calls).length, 0);
});

test("判別不能: 成功と失敗を合わせて3回で打ち止め（起動を繰り返さない）", async () => {
  const u = (id) => unknown(undefined, id);
  assert.equal(classify((await tick("18:30", { invest: [u(1), u(2)] })).calls), "dispatch");
  for (const invest of [
    [u(1), u(2), u(3)],
    [u(1), u(2), fail(3, "17:40", "17:45")],
    [u(1), fail(2, "17:30", "17:35"), fail(3, "17:40", "17:45")],
  ]) {
    const r = await tick("18:30", { invest });
    assert.equal(posts(r.calls).length, 0);
    assert.ok(r.warns.some((l) => /上限のため起動しない/.test(l)));
  }
  // 起動先の表示名がずっと判別不能でも、1日（5分刻みの全 tick）の起動は3回まで
  const history = [];
  let count = 0;
  for (let m = 17 * 60 + 30; m <= 19 * 60 + 25; m += 5) {
    const hhmm = `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}`;
    const r = await tick(hhmm, { invest: history });
    if (classify(r.calls) === "dispatch") history.push(unknown("x", ++count, hhmm, hhmm));
  }
  assert.equal(count, 3);
});

test("判別不能: 実行中は起動を止め、失敗は失敗に数える", async () => {
  const active = unknown(undefined, 1, "17:30", "17:31", "in_progress", null);
  assert.equal(classify((await tick("17:35", { invest: [active] })).calls), "none");
  const f = unknown(undefined, 2, "17:30", "17:40", "completed", "failure");
  assert.equal(classify((await tick("17:55", { invest: [f] })).calls), "none"); // 30分の待ち
  assert.equal(classify((await tick("18:10", { invest: [f] })).calls), "dispatch");
  const cancelled = unknown(undefined, 3, "17:30", "17:35", "completed", "cancelled");
  const r = await tick("17:40", { invest: [cancelled, cancelled, cancelled] });
  assert.equal(classify(r.calls), "dispatch");
});

test("最終確認: DRY の run は除外し、判別不能の成功は成功扱いにしない", async () => {
  const cases = [
    [[drySuccess()], /状態: 未起動/],
    [[dryRun(1, D, "20:00", "20:05", "in_progress", null)], /状態: 未起動/],
    [[dryFail(2, "19:00", "19:05")], /状態: 未起動/],
    [[drySuccess(), fail(3, "17:30", "17:40")], /状態: 失敗1回/],
    [[drySuccess(), run(4, D, "19:50", "20:00", "in_progress", null)], /状態: 実行中/],
    [[unknown(undefined)], /状態: 実運用の成功を確認できません/],
    [[unknown("x"), fail(5, "18:00", "18:10")], /状態: 実運用の成功を確認できません/],
  ];
  for (const [invest, expected] of cases) {
    const r = await tick("20:10", { invest });
    assert.equal(posts(r.calls).filter(isMail).length, 1, String(expected));
    const body = posts(r.calls).find(isMail).body;
    assert.match(body.text, expected);
    for (const w of FORBIDDEN) assert.equal((body.subject + body.text).includes(w), false, w);
  }
  for (const invest of [[ok()], [ok(), drySuccess()], [unknown(undefined), ok()]]) {
    const r = await tick("20:10", { invest });
    assert.equal(posts(r.calls).length, 0);
  }
});

test("DRY除外: Worker が DRY 設定のときも判定は同じで、POST は 0 回", async () => {
  const env = { MY_INVEST_DRY_RUN: "true" };
  const d = await tick("17:30", { invest: [drySuccess()] }, { env });
  assert.equal(posts(d.calls).length, 0);
  assert.ok(d.logs.some((l) => /\[DRY\].*起動する予定/.test(l)));
  const m = await tick("20:10", { invest: [drySuccess()] }, { env });
  assert.equal(posts(m.calls).length, 0);
  assert.ok(m.logs.some((l) => /\[DRY\].*メールを送る予定（状態: 未起動）/.test(l)));
});

// ---- 隔離（C19・C21）----

test("C19 既存3 cron のとき my-invest 向けの呼び出しは 0 回", async () => {
  mock.timers.enable({ apis: ["Date"], now: jstMs(D, "17:30") });
  try {
    for (const cron of ["30 7 * * 2-6", "30 9 * * 2-6", "0 11 * * 2-6"]) {
      const r = await invoke({ cron, scheduledTime: jstMs(D, "17:30"), env: MI_ENV, handler: scenario({}) });
      assert.equal(miCalls(r.calls).length, 0, cron);
    }
  } finally {
    mock.timers.reset();
  }
});

const BOOM = { toString() { throw new Error("boom"); } };

test("C21 my-invest が例外を投げても Kabu-Note は起動できる", async () => {
  const kn = [run(100, D, "16:30", "16:46", "completed", "success")];
  const r = await invoke({
    cron: KN_CRON, scheduledTime: jstMs(D, "17:30"),
    env: { ...MI_ENV, KABU_NOTE_DRY_RUN: "false", MY_INVEST_DRY_RUN: BOOM },
    handler: scenario({ screener: kn }),
  });
  assert.ok(r.errors.some((e) => /my-invest tick で予期しないエラー/.test(e)));
  assert.equal(posts(r.calls).filter((c) => KN_DISPATCH_RE.test(c.url)).length, 1);
  assert.equal(r.pending.length, 1);
});

test("C21 Kabu-Note が例外を投げても my-invest は起動できる", async () => {
  const r = await invoke({
    cron: KN_CRON, scheduledTime: jstMs(D, "17:30"),
    env: { ...MI_ENV, KABU_NOTE_DRY_RUN: BOOM },
    handler: scenario({ invest: [] }),
  });
  assert.ok(r.errors.some((e) => /kabu-note tick で予期しないエラー/.test(e)));
  assert.equal(posts(r.calls).filter(isDispatch).length, 1);
});

test("C21 screener 側に今日の run が無くても my-invest は独立して起動できる", async () => {
  const r = await tick("17:30", { invest: [], screener: [] }, { env: { KABU_NOTE_DRY_RUN: "false" } });
  assert.equal(classify(r.calls), "dispatch");
});
