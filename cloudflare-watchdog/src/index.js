/**
 * japan-stock-screener の日次バッチが確実に走るようにするための外部ウォッチドッグ。
 *
 * 背景: GitHub Actions の `schedule` トリガーは GitHub 公式ドキュメントで
 * 「負荷が高い時間帯は遅延・スキップされうる（保証されたタイミングではない）」
 * と明記されているベストエフォート機能で、実際に11時間以上の遅延や
 * 完全な未発火が発生した（2026-08-27〜28）。
 *
 * 対策として、GitHub の schedule イベントより優先度が高く扱われる
 * workflow_dispatch（API起動）を、Cloudflare Cron Triggers という
 * GitHub の外部にある確実なスケジューラから叩く2段構成にする。
 *
 * タイムライン（JST）:
 *   16:30  1回目起動（無条件で workflow_dispatch）
 *   18:30  今日分が成功していなければ 2回目起動
 *   20:00  今日分がまだ成功していなければ、管理者にメールでエラー通知
 *
 * 「今日分が成功しているか」は Discord通知の有無ではなく、
 * GitHub Actions の実行結果を直接APIで確認する（絶対原則5:
 * 沈黙による誤認を作らない、を「通知の有無」ではなく「実行結果の事実」で判定するため）。
 */

const CRON_FIRST_ATTEMPT = "30 7 * * 1-5";  // 16:30 JST
const CRON_RETRY = "30 9 * * 1-5";          // 18:30 JST
const CRON_FINAL_CHECK = "0 11 * * 1-5";    // 20:00 JST

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(handleScheduled(event, env));
  },

  // wrangler dev でのローカル確認用（本番では未使用）
  async fetch(request, env) {
    const url = new URL(request.url);
    const cron = url.searchParams.get("cron") || CRON_FIRST_ATTEMPT;
    await handleScheduled({ cron }, env);
    return new Response(`ok: simulated cron=${cron}\n`);
  },
};

async function handleScheduled(event, env) {
  const cron = event.cron;

  if (cron === CRON_FIRST_ATTEMPT) {
    console.log("[watchdog] 16:30 — 1回目起動（無条件）");
    await triggerWorkflow(env);
    return;
  }

  const todayJst = jstDateString(new Date());
  const state = await checkTodayStatus(env, todayJst);

  if (state === "success") {
    console.log(`[watchdog] ${todayJst} は既に成功済み。何もしない。`);
    return;
  }
  if (state === "active") {
    console.log(`[watchdog] ${todayJst} は現在実行中。重複起動を避けて何もしない。`);
    return;
  }

  if (cron === CRON_RETRY) {
    console.log("[watchdog] 18:30 — 未成功のため2回目起動");
    await triggerWorkflow(env);
    return;
  }

  if (cron === CRON_FINAL_CHECK) {
    console.log("[watchdog] 20:00 — 2回目も未成功。管理者にエラーメールを送信");
    await sendAlertEmail(env, todayJst);
    return;
  }

  console.warn(`[watchdog] 未知のcron文字列: ${cron}`);
}

/** JST（Asia/Tokyo）基準の YYYY-MM-DD を返す */
function jstDateString(date) {
  return new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date); // sv-SE ロケールは YYYY-MM-DD 形式を返す
}

/** GitHub Actions の実行結果から、今日分(JST)の状態を判定する */
async function checkTodayStatus(env, todayJst) {
  const url =
    `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}` +
    `/actions/workflows/${env.WORKFLOW_FILE}/runs?per_page=20`;

  const res = await fetch(url, { headers: githubHeaders(env) });
  if (!res.ok) {
    throw new Error(`GitHub runs取得失敗: ${res.status} ${await res.text()}`);
  }
  const body = await res.json();
  const runsToday = (body.workflow_runs || []).filter(
    (r) => jstDateString(new Date(r.created_at)) === todayJst
  );

  if (runsToday.some((r) => r.status !== "completed")) return "active";
  if (runsToday.some((r) => r.conclusion === "success")) return "success";
  return "missing"; // 今日分が無い、または全て失敗
}

/** workflow_dispatch で daily_screen.yml を起動する */
async function triggerWorkflow(env) {
  const url =
    `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}` +
    `/actions/workflows/${env.WORKFLOW_FILE}/dispatches`;

  const res = await fetch(url, {
    method: "POST",
    headers: githubHeaders(env),
    body: JSON.stringify({ ref: env.WORKFLOW_REF || "main" }),
  });
  if (!res.ok) {
    throw new Error(`workflow_dispatch失敗: ${res.status} ${await res.text()}`);
  }
  console.log("[watchdog] workflow_dispatch 送信成功");
}

function githubHeaders(env) {
  return {
    Authorization: `Bearer ${env.GITHUB_TOKEN}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "japan-stock-screener-watchdog",
    "Content-Type": "application/json",
  };
}

/** Resend経由で管理者にエラーメールを送信する */
async function sendAlertEmail(env, todayJst) {
  const actionsUrl = `https://github.com/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${env.WORKFLOW_FILE}`;
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: env.ALERT_FROM_EMAIL,
      to: env.ALERT_TO_EMAIL,
      subject: `[要確認] 日本株スクリーナー ${todayJst} 分が未配信です`,
      text:
        `${todayJst} のスクリーニングが16:30・18:30の2回の起動を経ても完了していません。\n\n` +
        `GitHub Actionsの実行状況を確認してください:\n${actionsUrl}\n\n` +
        `このメールは cloudflare-watchdog（絶対原則5: 沈黙による誤認を作らない）から自動送信されています。`,
    }),
  });
  if (!res.ok) {
    throw new Error(`Resend送信失敗: ${res.status} ${await res.text()}`);
  }
  console.log("[watchdog] 管理者アラートメール送信成功");
}
