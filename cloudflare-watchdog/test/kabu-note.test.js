// Kabu-Note tick のテスト（C2〜C8）。fetch はモック。時刻は event.scheduledTime で注入する。
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  ENV, KN_CRON, SCREENER_RUNS_RE, SCREENER_JOBS_RE, KN_RUNS_RE, KN_DISPATCH_RE,
  jstMs, run, invoke, posts,
} from "./helpers.js";

const D = "2026-11-17";

/** screener: runs配列 | {error:500}、jobs: "success"|"skipped"|"failure"|"error"|"none"、kabu: runs配列 */
function scenario({ screener = [], jobs = "success", kabu = [] }) {
  return (url, call) => {
    if (SCREENER_RUNS_RE.test(url)) {
      if (screener && screener.error) return { status: screener.error, body: "err" };
      return { body: { workflow_runs: screener } };
    }
    if (SCREENER_JOBS_RE.test(url)) {
      if (jobs === "error") return { status: 500, body: "err" };
      if (jobs === "none") return { body: { jobs: [{ name: "shard-screen", conclusion: "success" }] } };
      return { body: { jobs: [{ name: "check-market", conclusion: "success" }, { name: "aggregate-screen", conclusion: jobs }] } };
    }
    if (KN_RUNS_RE.test(url) && call.method === "GET") return { body: { workflow_runs: kabu } };
    if (KN_DISPATCH_RE.test(url) && call.method === "POST") return { status: 204, body: "" };
    if (/api\.resend\.com\/emails/.test(url) && call.method === "POST") return { body: { id: "x" } };
    return null;
  };
}

const scrOK = (end = "16:46") => [run(100, D, "16:30", end, "completed", "success")];
const kabu = (...r) => r;

const isDispatch = (c) => KN_DISPATCH_RE.test(c.url);
const isMail = (c) => /resend/.test(c.url);

async function tick(hhmm, sc, { date = D, env = {} } = {}) {
  return invoke({ cron: KN_CRON, scheduledTime: jstMs(date, hhmm), env: { KABU_NOTE_DRY_RUN: "false", ...env }, handler: scenario(sc) });
}

// [#, 時刻, シナリオ, 期待: "none"|"dispatch"|"mail"]
const TABLE = [
  [1, "16:40", { screener: scrOK() }, "none"],
  [2, "16:45", { screener: [] }, "none"],
  [3, "16:45", { screener: [run(100, D, "16:30", "16:45", "in_progress", null)] }, "none"],
  [4, "16:50", { screener: scrOK("16:46") }, "dispatch"],
  [5, "16:55", { screener: scrOK(), kabu: kabu(run(1, D, "16:50", "16:55", "in_progress", null)) }, "none"],
  [6, "17:00", { screener: scrOK(), kabu: kabu(run(1, D, "16:50", "16:53", "completed", "success")) }, "none"],
  [7, "17:00", { screener: scrOK("16:46"), kabu: kabu(run(1, D, "16:40", "16:43", "completed", "success")) }, "dispatch"],
  [8, "17:00", { screener: scrOK(), jobs: "skipped" }, "none"],
  [9, "17:20", { screener: scrOK(), kabu: kabu(run(1, D, "16:50", "17:05", "completed", "failure")) }, "none"],
  [10, "17:40", { screener: scrOK(), kabu: kabu(run(1, D, "16:50", "17:05", "completed", "failure")) }, "dispatch"],
  [11, "19:00", { screener: scrOK(), kabu: kabu(
    run(1, D, "16:50", "16:52", "completed", "failure"), run(2, D, "17:25", "17:27", "completed", "failure"),
    run(3, D, "18:00", "18:02", "completed", "failure"), run(4, D, "18:35", "18:37", "completed", "timed_out")) }, "none"],
  [12, "18:50", { screener: [run(100, D, "16:30", "16:40", "completed", "failure"), run(101, D, "18:30", "18:46", "completed", "success")] }, "dispatch"],
  [13, "17:00", { screener: scrOK("16:46"), kabu: kabu(run(9, "2026-11-18", "01:00", "01:03", "completed", "success", "schedule")) }, "dispatch"],
  [14, "20:00", { screener: scrOK() }, "none"],
  [15, "20:05", { screener: scrOK() }, "mail"],
  [15.1, "20:05", { screener: scrOK(), kabu: kabu(run(1, D, "16:50", "16:52", "completed", "failure")) }, "mail"],
  [15.2, "20:05", { screener: scrOK(), kabu: kabu(run(1, D, "19:50", "20:04", "in_progress", null)) }, "mail"],
  [16, "20:05", { screener: scrOK(), kabu: kabu(run(1, D, "16:50", "16:53", "completed", "success")) }, "none"],
  [17, "20:05", { screener: scrOK(), jobs: "skipped" }, "none"],
  [18, "20:05", { screener: [] }, "none"],
  [18.1, "20:05", { screener: [run(100, D, "16:30", "16:40", "completed", "failure")] }, "none"],
  [19, "20:05", { screener: { error: 500 } }, "mail"],
  [20, "20:10", { screener: scrOK() }, "none"],
];

function classify(calls) {
  const p = posts(calls);
  if (p.some(isDispatch)) return "dispatch";
  if (p.some(isMail)) return "mail";
  return "none";
}

test("C2 起動時刻の表", async () => {
  for (const [n, hhmm, sc, expected] of TABLE) {
    const r = await tick(hhmm, sc);
    assert.equal(classify(r.calls), expected, `#${n} ${hhmm}`);
    if (expected === "dispatch") {
      assert.equal(posts(r.calls).length, 1, `#${n}`);
      const body = posts(r.calls)[0].body;
      assert.equal(body.ref, "main");
      assert.deepEqual(body.inputs, { expected_snapshot_date: D }, `#${n}`);
    }
    if (expected === "mail") assert.equal(posts(r.calls).length, 1, `#${n}`);
  }
});

test("C2 #1/#20 窓の外は API 呼び出し 0 回", async () => {
  for (const hhmm of ["16:40", "20:10", "20:00", "21:00", "03:00"]) {
    const r = await tick(hhmm, { screener: scrOK() });
    assert.equal(r.calls.length, 0, hhmm);
  }
});

test("C2 #19 確認不能メールの文面", async () => {
  const r = await tick("20:05", { screener: { error: 500 } });
  assert.match(posts(r.calls)[0].body.text, /確認できませんでした/);
});

test("C3 JST の日付・時刻だけで決まる（UTC日付が違う・月末・年末年始・曜日違い）", async () => {
  // 2026-11-16T15:30Z = JST 11/17 00:30 は窓の外
  const r0 = await invoke({
    cron: KN_CRON, scheduledTime: Date.parse("2026-11-16T15:30:00Z"), handler: scenario({ screener: scrOK() }),
  });
  assert.equal(r0.calls.length, 0);

  const dates = ["2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-30", "2026-12-31", "2027-01-04"];
  for (const date of dates) {
    const sc = { screener: [run(100, date, "16:30", "16:46", "completed", "success")] };
    const r = await tick("16:50", sc, { date });
    assert.equal(classify(r.calls), "dispatch", date);
    assert.deepEqual(posts(r.calls)[0].body.inputs, { expected_snapshot_date: date });
    const rm = await tick("20:05", sc, { date });
    assert.equal(classify(rm.calls), "mail", date);
  }
  // 前日の screener run しか無ければ今日分とは見なさない
  const yesterdayOnly = { screener: [run(100, "2026-12-30", "16:30", "16:46", "completed", "success")] };
  const r1 = await tick("16:50", yesterdayOnly, { date: "2026-12-31" });
  assert.equal(classify(r1.calls), "none");
});

test("C3 kabu-note.js は new Date( を使わない", () => {
  const src = readFileSync(new URL("../src/kabu-note.js", import.meta.url), "utf8");
  assert.equal(/new Date\(/.test(src), false);
  assert.equal(/Date\.now\(/.test(src), false);
});

test("C4 DRY モードは GET のみ", async () => {
  for (const [n, hhmm, sc] of TABLE) {
    const r = await tick(hhmm, sc, { env: { KABU_NOTE_DRY_RUN: "true" } });
    assert.equal(posts(r.calls).length, 0, `#${n}`);
    assert.equal(r.calls.filter(isMail).length, 0, `#${n}`);
  }
  const r = await tick("16:50", { screener: scrOK() }, { env: { KABU_NOTE_DRY_RUN: "true" } });
  assert.ok(r.logs.some((l) => /\[DRY\].*起動する予定/.test(l)));
  const m = await tick("20:05", { screener: scrOK() }, { env: { KABU_NOTE_DRY_RUN: "true" } });
  assert.ok(m.logs.some((l) => /\[DRY\].*メールを送る予定/.test(l)));
});

test("C5 DISPATCH 段階の API エラー: POST 0 回・エラーがログに残り、例外は伝播しない", async () => {
  const r = await tick("16:50", { screener: { error: 500 } });
  assert.equal(posts(r.calls).length, 0);
  assert.ok(r.errors.some((e) => /DISPATCH段階でエラー/.test(e)));
  assert.equal(r.pending.length, 1);
});

test("C5 fetch が例外を投げても scheduled() は例外を出さない", async () => {
  const r = await invoke({
    cron: KN_CRON, scheduledTime: jstMs(D, "16:50"),
    handler: () => { throw new Error("network down"); },
  });
  assert.equal(posts(r.calls).length, 0);
  assert.ok(r.errors.length >= 1);
});

test("C5 dispatch が 422 のときは入力なしで再送しない", async () => {
  const handler = (url, call) => {
    if (KN_DISPATCH_RE.test(url)) return { status: 422, body: "Unexpected inputs" };
    return scenario({ screener: scrOK() })(url, call);
  };
  const r = await invoke({ cron: KN_CRON, scheduledTime: jstMs(D, "16:50"), env: { KABU_NOTE_DRY_RUN: "false" }, handler });
  assert.equal(posts(r.calls).length, 1);
  assert.ok(r.errors.some((e) => /workflow_dispatch失敗: 422/.test(e)));
});

test("C6 Kabu-Note の run 取得URLに event=workflow_dispatch が含まれる", async () => {
  const r = await tick("16:50", { screener: scrOK() });
  const g = r.calls.filter((c) => KN_RUNS_RE.test(c.url));
  assert.equal(g.length, 1);
  assert.match(g[0].url, /event=workflow_dispatch/);
});

test("C6 jobs 取得に失敗した場合は DISPATCH は fail open、FINAL は確認不能として通知", async () => {
  const r = await tick("16:50", { screener: scrOK(), jobs: "error" });
  assert.equal(classify(r.calls), "dispatch");
  const f = await tick("20:05", { screener: scrOK(), jobs: "error" });
  assert.equal(classify(f.calls), "mail");
  assert.match(posts(f.calls)[0].body.text, /確認できませんでした/);
});

test("C6 aggregate-screen が無い run（cache_warm 等）では起動しない", async () => {
  const r = await tick("16:50", { screener: scrOK(), jobs: "none" });
  assert.equal(classify(r.calls), "none");
});

test("C6 cancelled は失敗に数えない", async () => {
  const kb = kabu(
    run(1, D, "16:50", "17:05", "completed", "cancelled"), run(2, D, "17:06", "17:07", "completed", "cancelled"),
    run(3, D, "17:08", "17:09", "completed", "cancelled"), run(4, D, "17:10", "17:11", "completed", "cancelled"));
  const r = await tick("17:20", { screener: scrOK(), kabu: kb });
  assert.equal(classify(r.calls), "dispatch");
});

const FORBIDDEN = ["推奨", "おすすめ", "エントリーに", "買い時", "売り時", "狙い目", "すべき", "勝率"];

test("C7 メールの安全性", async () => {
  const states = [
    { screener: scrOK() },
    { screener: scrOK(), kabu: kabu(run(1, D, "16:50", "16:52", "completed", "failure")) },
    { screener: { error: 500 } },
  ];
  for (const sc of states) {
    const r = await tick("20:05", sc);
    const mail = posts(r.calls).find(isMail);
    assert.ok(mail);
    assert.equal(mail.body.to, ENV.ALERT_TO_EMAIL);
    assert.equal(mail.body.from, ENV.ALERT_FROM_EMAIL);
    const all = mail.body.subject + "\n" + mail.body.text;
    assert.match(all, new RegExp(D));
    assert.match(all, /https:\/\/github\.com\/test-owner\/kabu-repo\/actions\/workflows\/daily_update\.yml/);
    for (const bad of ["github_pat_", "ghp_", "re_", "eyJ", "dummy-"]) assert.equal(all.includes(bad), false, bad);
    for (const w of FORBIDDEN) assert.equal(all.includes(w), false, w);
  }
  // 20:05 以外の tick では送信 0
  for (const hhmm of ["16:45", "17:00", "19:55", "20:00", "20:10", "20:55"]) {
    const r = await tick(hhmm, { screener: scrOK() });
    assert.equal(r.calls.filter(isMail).length, 0, hhmm);
  }
});

test("C7 ソースに禁止語が無い", () => {
  for (const f of ["../src/kabu-note.js", "../src/index.js"]) {
    const src = readFileSync(new URL(f, import.meta.url), "utf8");
    for (const w of FORBIDDEN) assert.equal(src.includes(w), false, `${f}: ${w}`);
  }
});

test("C8 トークン選択（専用トークン優先、無ければ GITHUB_TOKEN）。値はログ・メールに出ない", async () => {
  const auth = (r, re) => r.calls.filter((c) => re.test(c.url)).map((c) => c.headers.Authorization);
  const withDedicated = await tick("16:50", { screener: scrOK() }, { env: { KABU_NOTE_GITHUB_TOKEN: "dummy-kabu-token" } });
  assert.deepEqual([...new Set(auth(withDedicated, KN_RUNS_RE))], ["Bearer dummy-kabu-token"]);
  assert.deepEqual([...new Set(auth(withDedicated, KN_DISPATCH_RE))], ["Bearer dummy-kabu-token"]);
  assert.deepEqual([...new Set(auth(withDedicated, SCREENER_RUNS_RE))], ["Bearer dummy-screener-token"]);
  const fallback = await tick("16:50", { screener: scrOK() });
  assert.deepEqual([...new Set(auth(fallback, KN_DISPATCH_RE))], ["Bearer dummy-screener-token"]);

  const failing = await tick("16:50", { screener: { error: 500 } }, { env: { KABU_NOTE_GITHUB_TOKEN: "dummy-kabu-token" } });
  for (const l of [...failing.logs, ...failing.warns, ...failing.errors]) {
    assert.equal(l.includes("dummy-kabu-token") || l.includes("dummy-screener-token"), false);
  }
  const mail = await tick("20:05", { screener: scrOK() }, { env: { KABU_NOTE_GITHUB_TOKEN: "dummy-kabu-token" } });
  const m = posts(mail.calls).find(isMail);
  assert.equal(JSON.stringify(m.body).includes("dummy-kabu-token"), false);
});

test("scheduledTime が無い（debug fetch 経由）場合は何もしない", async () => {
  const r = await invoke({ cron: KN_CRON, scheduledTime: undefined, handler: scenario({}) });
  assert.equal(r.calls.length, 0);
});

test("DRY は安全側: 未設定・不正値は DRY、\"false\" だけが実起動", async () => {
  const raw = (dry) => invoke({
    cron: KN_CRON, scheduledTime: jstMs(D, "16:50"),
    env: dry === undefined ? {} : { KABU_NOTE_DRY_RUN: dry },
    handler: scenario({ screener: scrOK() }),
  });
  for (const v of [undefined, "", "TRUE", "0", "no"]) {
    assert.equal(posts((await raw(v)).calls).length, 0, `dry=${v}`);
  }
  assert.equal(posts((await raw("false")).calls).filter(isDispatch).length, 1);
});

test("トークン未設定: Bearer undefined を送らず、POST 0 回・エラーがログに残る", async () => {
  const r = await invoke({
    cron: KN_CRON, scheduledTime: jstMs(D, "16:50"),
    env: { KABU_NOTE_DRY_RUN: "false", KABU_NOTE_GITHUB_TOKEN: "", GITHUB_TOKEN: "" },
    handler: scenario({ screener: scrOK() }),
  });
  assert.equal(posts(r.calls).length, 0);
  assert.equal(r.calls.some((c) => String(c.headers && c.headers.Authorization).includes("undefined")), false);
  assert.ok(r.errors.some((l) => /トークン未設定/.test(l)));
});
