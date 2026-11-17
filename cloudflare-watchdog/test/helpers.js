// テスト共通: fetch モックと scheduled() 呼び出し。実ネットワークには出ない（未モックURLは失敗）。
// このリポジトリは PUBLIC のため、値はすべて架空。
import worker from "../src/index.js";

export const ENV = {
  GITHUB_OWNER: "test-owner",
  GITHUB_REPO: "screener-repo",
  WORKFLOW_FILE: "daily_screen.yml",
  WORKFLOW_REF: "main",
  KABU_NOTE_REPO: "kabu-repo",
  KABU_NOTE_WORKFLOW_FILE: "daily_update.yml",
  ALERT_FROM_EMAIL: "from@example.invalid",
  ALERT_TO_EMAIL: "to@example.invalid",
  GITHUB_TOKEN: "dummy-screener-token",
  RESEND_API_KEY: "dummy-resend-key",
};

export const KN_CRON = "*/5 7-11 * * 2-6";
export const SCREENER_RUNS_RE = /\/repos\/test-owner\/screener-repo\/actions\/workflows\/daily_screen\.yml\/runs/;
export const SCREENER_JOBS_RE = /\/repos\/test-owner\/screener-repo\/actions\/runs\/(\d+)\/jobs/;
export const KN_RUNS_RE = /\/repos\/test-owner\/kabu-repo\/actions\/workflows\/daily_update\.yml\/runs/;
export const KN_DISPATCH_RE = /\/repos\/test-owner\/kabu-repo\/actions\/workflows\/daily_update\.yml\/dispatches/;

/** "YYYY-MM-DD" と "HH:MM"(JST) から ms */
export function jstMs(date, hhmm) {
  return Date.parse(`${date}T${hhmm}:00+09:00`);
}
export function jstIso(date, hhmm) {
  return new Date(jstMs(date, hhmm)).toISOString();
}

export function run(id, date, createdHhmm, endHhmm, status, conclusion, event = "workflow_dispatch") {
  return {
    id,
    event,
    status,
    conclusion,
    created_at: jstIso(date, createdHhmm),
    updated_at: jstIso(date, endHhmm || createdHhmm),
  };
}

/**
 * handler(url, init) => { status, body } を受ける fetch モックを仕込み、scheduled() を呼ぶ。
 * 戻り値: { calls:[{url,method,body,headers}], logs, errors, warns }
 */
export async function invoke({ cron, scheduledTime, env = {}, handler }) {
  const calls = [];
  const logs = [];
  const warns = [];
  const errors = [];
  const origFetch = globalThis.fetch;
  const origLog = console.log, origWarn = console.warn, origErr = console.error;
  globalThis.fetch = async (url, init = {}) => {
    const call = {
      url: String(url),
      method: init.method || "GET",
      body: init.body ? JSON.parse(init.body) : undefined,
      headers: init.headers || {},
    };
    calls.push(call);
    const r = handler(call.url, call);
    if (!r) throw new Error(`未モックのURL: ${call.method} ${call.url}`);
    return new Response(typeof r.body === "string" ? r.body : JSON.stringify(r.body ?? {}), {
      status: r.status ?? 200,
    });
  };
  console.log = (...a) => logs.push(a.join(" "));
  console.warn = (...a) => warns.push(a.join(" "));
  console.error = (...a) => errors.push(a.join(" "));
  const pending = [];
  try {
    await worker.scheduled({ cron, scheduledTime }, { ...ENV, ...env }, { waitUntil: (p) => pending.push(p) });
    await Promise.allSettled(pending);
  } finally {
    globalThis.fetch = origFetch;
    console.log = origLog;
    console.warn = origWarn;
    console.error = origErr;
  }
  return { calls, logs, warns, errors, pending };
}

export const posts = (calls) => calls.filter((c) => c.method === "POST");
