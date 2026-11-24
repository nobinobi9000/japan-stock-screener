// my-invest tick のテスト（C19〜C22）。fetch はモック。時刻は event.scheduledTime で注入する。
// このリポジトリは PUBLIC のため、値はすべて架空。
import test, { mock } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  ENV, KN_CRON, KN_RUNS_RE, KN_DISPATCH_RE, SCREENER_RUNS_RE, SCREENER_JOBS_RE,
  jstMs, run, invoke, posts,
} from "./helpers.js";

const D = "2026-11-18";
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
