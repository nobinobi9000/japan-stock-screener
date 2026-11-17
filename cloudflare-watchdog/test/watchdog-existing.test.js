// C1: 既存3 cron の挙動の固定（回帰テスト）。Kabu-Note 向け URL への呼び出しが 0 回であることも確認する。
// 既存経路は new Date() を使うため、Date を固定して実行する。
import test, { mock } from "node:test";
import assert from "node:assert/strict";
import { ENV, run, invoke, posts } from "./helpers.js";

const D = "2026-11-17";
const NOW = Date.parse(`${D}T16:30:00+09:00`);
const SCR_DISPATCH = /\/repos\/test-owner\/screener-repo\/actions\/workflows\/daily_screen\.yml\/dispatches/;
const SCR_RUNS = /\/repos\/test-owner\/screener-repo\/actions\/workflows\/daily_screen\.yml\/runs/;
const kabuCalls = (calls) => calls.filter((c) => /kabu-repo/.test(c.url));

function handlerWith(runs) {
  return (url, call) => {
    if (SCR_RUNS.test(url)) return { body: { workflow_runs: runs } };
    if (SCR_DISPATCH.test(url) && call.method === "POST") return { status: 204, body: "" };
    if (/api\.resend\.com\/emails/.test(url) && call.method === "POST") return { body: { id: "x" } };
    return null;
  };
}

test.beforeEach(() => mock.timers.enable({ apis: ["Date"], now: NOW }));
test.afterEach(() => mock.timers.reset());

test("C1 30 7 * * 2-6: 無条件に screener を dispatch 1回", async () => {
  const r = await invoke({ cron: "30 7 * * 2-6", scheduledTime: NOW, handler: handlerWith([]) });
  assert.equal(posts(r.calls).length, 1);
  assert.match(r.calls[0].url, SCR_DISPATCH);
  assert.deepEqual(r.calls[0].body, { ref: "main" });
  assert.equal(kabuCalls(r.calls).length, 0);
});

test("C1 30 9 * * 2-6: 成功/実行中は POST 0、未成功は POST 1", async () => {
  const ok = [run(1, D, "16:30", "16:45", "completed", "success")];
  const active = [run(1, D, "16:30", "16:45", "in_progress", null)];
  const failed = [run(1, D, "16:30", "16:45", "completed", "failure")];
  for (const [runs, n] of [[ok, 0], [active, 0], [failed, 1], [[], 1]]) {
    const r = await invoke({ cron: "30 9 * * 2-6", scheduledTime: NOW, handler: handlerWith(runs) });
    assert.equal(posts(r.calls).length, n);
    assert.equal(kabuCalls(r.calls).length, 0);
  }
});

test("C1 0 11 * * 2-6: 成功ならメール 0、未成功なら Resend 1通", async () => {
  const ok = [run(1, D, "16:30", "16:45", "completed", "success")];
  const r1 = await invoke({ cron: "0 11 * * 2-6", scheduledTime: NOW, handler: handlerWith(ok) });
  assert.equal(posts(r1.calls).length, 0);
  const r2 = await invoke({ cron: "0 11 * * 2-6", scheduledTime: NOW, handler: handlerWith([]) });
  const p = posts(r2.calls);
  assert.equal(p.length, 1);
  assert.match(p[0].url, /api\.resend\.com\/emails/);
  assert.equal(p[0].body.to, ENV.ALERT_TO_EMAIL);
  assert.equal(kabuCalls(r2.calls).length + kabuCalls(r1.calls).length, 0);
});

test("C1 未知の cron 文字列: POST 0 回で警告のみ", async () => {
  const r = await invoke({ cron: "15 3 * * 2-6", scheduledTime: NOW, handler: handlerWith([]) });
  assert.equal(posts(r.calls).length, 0);
  assert.ok(r.warns.some((w) => /未知のcron文字列/.test(w)));
  assert.equal(kabuCalls(r.calls).length, 0);
});

test("C1 既存分岐は曜日部分に依存しない（分 時のみ）", async () => {
  const r = await invoke({ cron: "30 7 * * 1-5", scheduledTime: NOW, handler: handlerWith([]) });
  assert.equal(posts(r.calls).length, 1);
});

test("C5 Kabu-Note 側の例外があっても既存分岐は同一プロセスで動く", async () => {
  const bad = await invoke({
    cron: "*/5 7-11 * * 2-6", scheduledTime: Date.parse(`${D}T16:50:00+09:00`),
    handler: () => { throw new Error("boom"); },
  });
  assert.equal(posts(bad.calls).length, 0);
  const r = await invoke({ cron: "30 7 * * 2-6", scheduledTime: NOW, handler: handlerWith([]) });
  assert.equal(posts(r.calls).length, 1);
});
