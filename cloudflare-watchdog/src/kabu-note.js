/**
 * Kabu-Note の日次バッチ(daily_update.yml)を、screener の完了を検知してから起動する。
 *
 * 背景: Kabu-Note 側の GitHub `schedule` は 5〜10 時間遅れで起動するのが常態で、
 * 終値の反映が深夜になっていた。screener と同じく Cloudflare Cron から
 * workflow_dispatch で起動する。
 *
 * 方式（検知型）: 5分おきの tick で「screener の今日分が成功したか」を GitHub の run 結果から
 * 毎回導出し、成功を確認できたら Kabu-Note を起動する。Worker は状態を持たない。
 *   16:45〜19:55  DISPATCH 段階（起動・再試行）
 *   20:05         FINAL 段階（未完了なら管理者にメール。1日1回）
 *
 * 分離方針: このモジュールは screener 経路(index.js の既存3 cron)から独立している。
 * 時刻は event.scheduledTime（予定時刻）だけから作り、現在時刻には依存しない。
 * 例外は呼び出し側(index.js)で握り、screener 経路へ伝播させない。
 *
 * 公開リポジトリのため、メール・ログには日付・状態・Actions の URL だけを出す。
 */

export const KABU_NOTE_CRON_SLOT = "*/5 7-11"; // wrangler.toml の "*/5 7-11 * * 2-6"（UTC）

const WINDOW_START_MIN = 16 * 60 + 45; // 16:45 JST
const WINDOW_END_MIN = 19 * 60 + 55;   // 19:55 JST（これ以降は起動しない）
const FINAL_CHECK_MIN = 20 * 60 + 5;   // 20:05 JST
const MAX_ATTEMPTS = 4;                // 1日の起動(失敗)上限
const RETRY_BACKOFF_MIN = 30;          // 失敗 run の完了から次の起動までの間隔
const AGGREGATE_JOB_NAME = "aggregate-screen";

const jstFormatter = new Intl.DateTimeFormat("sv-SE", {
  timeZone: "Asia/Tokyo",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

/** 時刻(ms)から JST の { date: "YYYY-MM-DD", minutes: 0..1439 } を作る */
function jstParts(ms) {
  const p = {};
  for (const { type, value } of jstFormatter.formatToParts(ms)) p[type] = value;
  return {
    date: `${p.year}-${p.month}-${p.day}`,
    minutes: Number(p.hour) * 60 + Number(p.minute),
  };
}

function jstDateOf(isoString) {
  return jstParts(Date.parse(isoString)).date;
}

function tokenFor(env) {
  const token = env.KABU_NOTE_GITHUB_TOKEN || env.GITHUB_TOKEN;
  // 未設定のまま "Bearer undefined" を送らない（呼び出し側の catch でログに残る）
  if (!token) throw new Error("GitHubトークン未設定（KABU_NOTE_GITHUB_TOKEN / GITHUB_TOKEN）");
  return token;
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "japan-stock-screener-watchdog",
    "Content-Type": "application/json",
  };
}

async function failure(what, res) {
  // 本文は先頭だけ。トークンはリクエストヘッダにしか無く、ここには出ない。
  const body = (await res.text()).slice(0, 200);
  return new Error(`${what}: ${res.status} ${body}`);
}

async function getJson(url, token, what) {
  const res = await fetch(url, { headers: headers(token) });
  if (!res.ok) throw await failure(what, res);
  return res.json();
}

/** screener の今日分(JST)の状態。{ state: "none"|"active"|"failed"|"success", successRun } */
async function screenerToday(env, today) {
  const url =
    `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}` +
    `/actions/workflows/${env.WORKFLOW_FILE}/runs?per_page=20`;
  const body = await getJson(url, env.GITHUB_TOKEN, "screener runs取得失敗");
  const runs = (body.workflow_runs || []).filter((r) => jstDateOf(r.created_at) === today);
  if (runs.length === 0) return { state: "none" };
  if (runs.some((r) => r.status !== "completed")) return { state: "active" };
  const ok = runs
    .filter((r) => r.conclusion === "success")
    .sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at));
  if (ok.length === 0) return { state: "failed" };
  return { state: "success", successRun: ok[0] };
}

/** aggregate-screen ジョブの結論。取得できなければ例外 */
async function aggregateConclusion(env, runId) {
  const url =
    `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}` +
    `/actions/runs/${runId}/jobs?per_page=30`;
  const body = await getJson(url, env.GITHUB_TOKEN, "screener jobs取得失敗");
  const job = (body.jobs || []).find((j) => j.name === AGGREGATE_JOB_NAME);
  return job ? job.conclusion : null; // null=該当ジョブ無し（cache_warm 等）
}

/**
 * Kabu-Note の run のうち、event=workflow_dispatch かつ screener 完了(tS)以後に作成されたものだけ。
 * 旧 schedule の遅延 run（翌日の日付で作成される）を「今日分」と誤認しないため。
 */
async function kabuNoteRunsSince(env, tS) {
  const url =
    `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.KABU_NOTE_REPO}` +
    `/actions/workflows/${env.KABU_NOTE_WORKFLOW_FILE}/runs?event=workflow_dispatch&per_page=20`;
  const body = await getJson(url, tokenFor(env), "Kabu-Note runs取得失敗");
  const runs = (body.workflow_runs || []).filter(
    (r) => (r.event === undefined || r.event === "workflow_dispatch") && Date.parse(r.created_at) >= tS
  );
  const summary = {
    success: runs.some((r) => r.status === "completed" && r.conclusion === "success"),
    active: runs.some((r) => r.status !== "completed"),
    // cancelled は concurrency による置換なので失敗に数えない
    failures: runs.filter(
      (r) => r.status === "completed" && (r.conclusion === "failure" || r.conclusion === "timed_out")
    ),
  };
  summary.lastFailureEnd = summary.failures.reduce(
    (max, r) => Math.max(max, Date.parse(r.updated_at)),
    0
  );
  return summary;
}

async function dispatchKabuNote(env, today) {
  const url =
    `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.KABU_NOTE_REPO}` +
    `/actions/workflows/${env.KABU_NOTE_WORKFLOW_FILE}/dispatches`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers(tokenFor(env)),
    body: JSON.stringify({
      ref: env.WORKFLOW_REF || "main",
      inputs: { expected_snapshot_date: today },
    }),
  });
  // 入力が未定義だった場合の 422 などは、入力なしで再送せず失敗として扱う（沈黙を避ける）
  if (!res.ok) throw await failure("Kabu-Note workflow_dispatch失敗", res);
}

// 安全側: 明示的に "false" のときだけ実起動する。未設定・不正値は DRY（GET のみ）。
function isDry(env) {
  return String(env.KABU_NOTE_DRY_RUN ?? "").trim().toLowerCase() !== "false";
}

/** @returns {Promise<string>} 何をしたか（テスト・ログ用）: skip / dispatch / mail / ... */
export async function kabuNoteTick(scheduledTime, env) {
  if (typeof scheduledTime !== "number" || Number.isNaN(scheduledTime)) {
    console.warn("[kabu-note] scheduledTime が無いため何もしない");
    return "skip:no-time";
  }
  const { date: today, minutes } = jstParts(scheduledTime);

  if (minutes >= WINDOW_START_MIN && minutes <= WINDOW_END_MIN) {
    return dispatchStage(env, today, scheduledTime);
  }
  if (minutes === FINAL_CHECK_MIN) {
    return finalStage(env, today);
  }
  return "skip:out-of-window";
}

async function dispatchStage(env, today, nowMs) {
  const dry = isDry(env);
  try {
    const scr = await screenerToday(env, today);
    if (scr.state !== "success") {
      console.log(`[kabu-note] ${today} screener=${scr.state}。起動しない。`);
      return `skip:screener-${scr.state}`;
    }
    const tS = Date.parse(scr.successRun.updated_at);

    try {
      const conclusion = await aggregateConclusion(env, scr.successRun.id);
      if (conclusion !== "success") {
        console.log(`[kabu-note] ${today} ${AGGREGATE_JOB_NAME}=${conclusion}（休場日など）。起動しない。`);
        return "skip:not-screened";
      }
    } catch (e) {
      // 取得できないときは起動を止めない（Kabu-Note は冪等。起動して害は小さい）
      console.warn(`[kabu-note] jobs確認に失敗したため続行: ${e.message}`);
    }

    const kn = await kabuNoteRunsSince(env, tS);
    if (kn.success) return "skip:done";
    if (kn.active) {
      console.log(`[kabu-note] ${today} 実行中。起動しない。`);
      return "skip:active";
    }
    if (kn.failures.length >= MAX_ATTEMPTS) {
      console.warn(`[kabu-note] ${today} 失敗が${kn.failures.length}回。上限のため起動しない（20:05に通知）。`);
      return "skip:max-attempts";
    }
    if (kn.failures.length > 0 && nowMs - kn.lastFailureEnd < RETRY_BACKOFF_MIN * 60 * 1000) {
      console.log(`[kabu-note] ${today} 直近の失敗から${RETRY_BACKOFF_MIN}分未満。再試行を待つ。`);
      return "skip:backoff";
    }

    if (dry) {
      console.log(`[kabu-note][DRY] ${today} Kabu-Note を起動する予定（expected_snapshot_date=${today}）。送信しない。`);
      return "dry:dispatch";
    }
    await dispatchKabuNote(env, today);
    console.log(`[kabu-note] ${today} workflow_dispatch 送信成功（失敗${kn.failures.length}回後）`);
    return "dispatch";
  } catch (e) {
    // 握りつぶさずログに残す。5分後の tick が自然な再試行になる
    console.error(`[kabu-note] DISPATCH段階でエラー: ${e.message}`);
    return "error";
  }
}

async function finalStage(env, today) {
  const dry = isDry(env);
  let state;
  try {
    const scr = await screenerToday(env, today);
    if (scr.state !== "success") {
      console.log(`[kabu-note] ${today} screener=${scr.state}。Kabu-Note向けの通知は出さない（screener側の通知が担当）。`);
      return `skip:screener-${scr.state}`;
    }
    const conclusion = await aggregateConclusion(env, scr.successRun.id);
    if (conclusion !== "success") {
      console.log(`[kabu-note] ${today} ${AGGREGATE_JOB_NAME}=${conclusion}（休場日など）。通知しない。`);
      return "skip:not-screened";
    }
    const kn = await kabuNoteRunsSince(env, Date.parse(scr.successRun.updated_at));
    if (kn.success) {
      console.log(`[kabu-note] ${today} 反映済み。通知しない。`);
      return "skip:done";
    }
    state = kn.active
      ? "実行中"
      : kn.failures.length > 0
        ? `失敗${kn.failures.length}回`
        : "未起動";
  } catch (e) {
    console.error(`[kabu-note] FINAL段階でエラー: ${e.message}`);
    state = "確認できませんでした（GitHub APIの取得に失敗）";
  }

  if (dry) {
    console.log(`[kabu-note][DRY] ${today} 管理者へメールを送る予定（状態: ${state}）。送信しない。`);
    return "dry:mail";
  }
  try {
    await sendMail(env, today, state);
    console.log("[kabu-note] 管理者へ通知メール送信成功");
    return "mail";
  } catch (e) {
    console.error(`[kabu-note] 通知メール送信に失敗: ${e.message}`);
    return "error";
  }
}

async function sendMail(env, today, state) {
  const actionsUrl =
    `https://github.com/${env.GITHUB_OWNER}/${env.KABU_NOTE_REPO}` +
    `/actions/workflows/${env.KABU_NOTE_WORKFLOW_FILE}`;
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: env.ALERT_FROM_EMAIL,
      to: env.ALERT_TO_EMAIL,
      subject: `[要確認] Kabu-Note ${today} 分の株価反映が未完了です`,
      text:
        `日付: ${today}\n` +
        `状態: ${state}\n\n` +
        `GitHub Actionsの実行状況:\n${actionsUrl}\n\n` +
        `このメールは cloudflare-watchdog から自動送信されています。`,
    }),
  });
  if (!res.ok) throw await failure("Resend送信失敗", res);
}
