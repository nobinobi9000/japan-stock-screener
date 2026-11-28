/**
 * 別リポジトリの平日チェック(workflow_dispatch のみで動く workflow)を、定刻に起動する。
 *
 * 方式(検知型・kabu-note.js と同じ設計): 5分おきの tick で「今日(JST)の run が成功したか」を
 * GitHub の run 結果から毎回導出する。Worker は状態を持たない。
 * screener や Kabu-Note の結果には依存しない(独立した判定)。
 *   17:30〜19:25  DISPATCH 段階（起動・再試行。失敗の完了から30分あけ、上限3回で打ち止め）
 *   20:10         FINAL 段階（今日の実運用の成功 run が無ければ管理者にメール。1日1回）
 *
 * 休場日の判定はここではしない。起動先が休場・データ未着を自分で判定して正常終了する。
 * 同じ日に実運用の成功 run が1回あれば再起動しない（冪等）。cancelled は失敗に数えない。
 *
 * run の区別: 起動先の run-name が表示名(display_title)に入れる "dry_run=true|false" で分ける。
 *   true     … 成功・実行中・失敗のどの判定にも使わない
 *   false    … 実運用の run
 *   判別不能 … 成功扱いにしない（黙って止まらないため）。実行中・失敗には数え、
 *              成功した分は失敗と合わせて1日の上限に数える（起動の繰り返しを防ぐ）。
 *              二重通知は起動先が同じデータ日付を再通知しないことで防ぐ。
 *
 * 分離方針: screener 経路(既存3 cron)と Kabu-Note から独立している。
 * 時刻は event.scheduledTime（予定時刻）だけから作り、現在時刻には依存しない。
 * 例外は呼び出し側(index.js)で握り、他の経路へ伝播させない。
 *
 * 公開リポジトリのため、メール・ログには日付・状態・Actions の URL だけを出す。
 * 起動先の秘密・個人データは、このファイルにも設定にも書かない。
 */

export const MY_INVEST_CRON_SLOT = "*/5 7-11"; // wrangler.toml の "*/5 7-11 * * 2-6"（UTC）

const WINDOW_START_MIN = 17 * 60 + 30; // 17:30 JST
const WINDOW_END_MIN = 19 * 60 + 25;   // 19:25 JST（これ以降は起動しない）
const FINAL_CHECK_MIN = 20 * 60 + 10;  // 20:10 JST
const MAX_ATTEMPTS = 3;                // 1日の上限（失敗＋判別不能の成功。達したら起動しない）
const RETRY_BACKOFF_MIN = 30;          // 失敗 run の完了から次の起動までの間隔

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
  // GITHUB_TOKEN へはフォールバックしない（別リポジトリへの権限が無く、最小権限にするため）。
  // 未設定のまま "Bearer undefined" を送らない。
  const token = env.MY_INVEST_GITHUB_TOKEN;
  if (!token) throw new Error("GitHubトークン未設定（MY_INVEST_GITHUB_TOKEN）");
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

function repoBase(env) {
  return `${env.GITHUB_OWNER}/${env.MY_INVEST_REPO}`;
}

/** 表示名から run の種類を返す: "dry" | "live" | "unknown" */
function runKind(run) {
  const m = /\bdry_run=(true|false)\b/.exec(String(run.display_title ?? ""));
  if (!m) return "unknown";
  return m[1] === "true" ? "dry" : "live";
}

/** 今日(JST)に作成された workflow_dispatch の run の要約（DRY の run は含めない） */
async function runsToday(env, today, token) {
  const url =
    `https://api.github.com/repos/${repoBase(env)}` +
    `/actions/workflows/${env.MY_INVEST_WORKFLOW_FILE}/runs?event=workflow_dispatch&per_page=20`;
  const res = await fetch(url, { headers: headers(token) });
  if (!res.ok) throw await failure("my-invest runs取得失敗", res);
  const body = await res.json();
  const runs = (body.workflow_runs || []).filter(
    (r) =>
      (r.event === undefined || r.event === "workflow_dispatch") &&
      jstDateOf(r.created_at) === today &&
      runKind(r) !== "dry"
  );
  const succeeded = runs.filter((r) => r.status === "completed" && r.conclusion === "success");
  const summary = {
    success: succeeded.some((r) => runKind(r) === "live"),
    unknownSuccess: succeeded.filter((r) => runKind(r) === "unknown").length,
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

async function dispatchRun(env, token) {
  const url =
    `https://api.github.com/repos/${repoBase(env)}` +
    `/actions/workflows/${env.MY_INVEST_WORKFLOW_FILE}/dispatches`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers(token),
    // dry_run は必ず明示する（起動先の既定は true のため、省略すると実運用にならない）
    body: JSON.stringify({ ref: env.WORKFLOW_REF || "main", inputs: { dry_run: "false" } }),
  });
  // 入力が未定義だった場合の 422 などは、入力なしで再送せず失敗として扱う（沈黙を避ける）
  if (!res.ok) throw await failure("my-invest workflow_dispatch失敗", res);
}

// 安全側: 明示的に "false" のときだけ実起動する。未設定・不正値は DRY（GET のみ）。
function isDry(env) {
  return String(env.MY_INVEST_DRY_RUN ?? "").trim().toLowerCase() !== "false";
}

/** @returns {Promise<string>} 何をしたか（テスト・ログ用）: skip / dispatch / mail / ... */
export async function myInvestTick(scheduledTime, env) {
  if (typeof scheduledTime !== "number" || Number.isNaN(scheduledTime)) {
    console.warn("[my-invest] scheduledTime が無いため何もしない");
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
    const token = tokenFor(env);
    const r = await runsToday(env, today, token);
    if (r.success) {
      console.log(`[my-invest] ${today} 成功済み。起動しない。`);
      return "skip:done";
    }
    if (r.unknownSuccess > 0) {
      console.warn(
        `[my-invest] ${today} dry_run を判別できない成功 run が${r.unknownSuccess}件。成功扱いにしない（起動先の run-name を確認）。`
      );
    }
    if (r.active) {
      console.log(`[my-invest] ${today} 実行中。起動しない。`);
      return "skip:active";
    }
    if (r.failures.length + r.unknownSuccess >= MAX_ATTEMPTS) {
      console.warn(
        `[my-invest] ${today} 失敗${r.failures.length}回・判別不能の成功${r.unknownSuccess}回。上限のため起動しない（20:10に通知）。`
      );
      return "skip:max-attempts";
    }
    if (r.failures.length > 0 && nowMs - r.lastFailureEnd < RETRY_BACKOFF_MIN * 60 * 1000) {
      console.log(`[my-invest] ${today} 直近の失敗から${RETRY_BACKOFF_MIN}分未満。再試行を待つ。`);
      return "skip:backoff";
    }

    if (dry) {
      console.log(`[my-invest][DRY] ${today} 平日チェックを起動する予定（dry_run=false）。送信しない。`);
      return "dry:dispatch";
    }
    await dispatchRun(env, token);
    console.log(`[my-invest] ${today} workflow_dispatch 送信成功（失敗${r.failures.length}回後）`);
    return "dispatch";
  } catch (e) {
    // 握りつぶさずログに残す。5分後の tick が自然な再試行になる
    console.error(`[my-invest] DISPATCH段階でエラー: ${e.message}`);
    return "error";
  }
}

async function finalStage(env, today) {
  const dry = isDry(env);
  let token;
  try {
    token = tokenFor(env);
  } catch (e) {
    // トークンが無いと確認も起動もできない。誤送信を避けて止まる（エラーはログに残す）
    console.error(`[my-invest] FINAL段階でエラー: ${e.message}`);
    return "error";
  }
  let state;
  try {
    const r = await runsToday(env, today, token);
    if (r.success) {
      console.log(`[my-invest] ${today} 成功済み。通知しない。`);
      return "skip:done";
    }
    state = r.active
      ? "実行中"
      : r.unknownSuccess > 0
        ? "実運用の成功を確認できません（dry_run の表示がない run が成功）"
        : r.failures.length > 0
          ? `失敗${r.failures.length}回`
          : "未起動";
  } catch (e) {
    console.error(`[my-invest] FINAL段階でエラー: ${e.message}`);
    state = "確認できませんでした（GitHub APIの取得に失敗）";
  }

  if (dry) {
    console.log(`[my-invest][DRY] ${today} 管理者へメールを送る予定（状態: ${state}）。送信しない。`);
    return "dry:mail";
  }
  try {
    await sendMail(env, today, state);
    console.log("[my-invest] 管理者へ通知メール送信成功");
    return "mail";
  } catch (e) {
    console.error(`[my-invest] 通知メール送信に失敗: ${e.message}`);
    return "error";
  }
}

async function sendMail(env, today, state) {
  const actionsUrl =
    `https://github.com/${repoBase(env)}` +
    `/actions/workflows/${env.MY_INVEST_WORKFLOW_FILE}`;
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: env.ALERT_FROM_EMAIL,
      to: env.ALERT_TO_EMAIL,
      subject: `[要確認] my-invest ${today} 分の平日チェックが未完了です`,
      text:
        `日付: ${today}\n` +
        `状態: ${state}\n\n` +
        `GitHub Actionsの実行状況:\n${actionsUrl}\n\n` +
        `このメールは cloudflare-watchdog から自動送信されています。`,
    }),
  });
  if (!res.ok) throw await failure("Resend送信失敗", res);
}
