// C23: wrangler.toml の静的検査（my-invest 追加分。TOMLパーサに依存しない簡易検査）
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const toml = readFileSync(new URL("../wrangler.toml", import.meta.url), "utf8");
const m = toml.match(/^crons\s*=\s*\[(.*?)\]/ms);
const crons = [...m[1].matchAll(/"([^"]+)"/g)].map((x) => x[1]);
const vars = toml.slice(toml.indexOf("[vars]"), toml.indexOf("[observability]"));
const varMap = Object.fromEntries([...vars.matchAll(/^([A-Z_]+)\s*=\s*"([^"]*)"/gm)].map((x) => [x[1], x[2]]));

test("C23 cron は既存4本と文字列一致（my-invest で増やさない）", () => {
  assert.deepEqual(crons, ["30 7 * * 2-6", "30 9 * * 2-6", "0 11 * * 2-6", "*/5 7-11 * * 2-6"]);
});

test("C23 workers_dev=false のまま", () => {
  assert.match(toml, /^workers_dev\s*=\s*false/m);
});

test("C23 my-invest の vars: 既定は DRY、トークンは vars に無い", () => {
  assert.equal(varMap.MY_INVEST_REPO, "my-invest-signal");
  assert.equal(varMap.MY_INVEST_WORKFLOW_FILE, "weekday_check.yml");
  assert.equal(varMap.MY_INVEST_DRY_RUN, "true");
  assert.equal("MY_INVEST_GITHUB_TOKEN" in varMap, false);
  assert.equal(/^MY_INVEST_GITHUB_TOKEN\s*=/m.test(toml), false);
});

test("C23 vars に秘密様の値が無い", () => {
  for (const v of Object.values(varMap)) for (const bad of ["github_pat_", "ghp_", "re_", "eyJ"]) {
    assert.equal(v.includes(bad), false, `${v}: ${bad}`);
  }
});

test("C23 コードは env.MY_INVEST_GITHUB_TOKEN のみを使い GITHUB_TOKEN へフォールバックしない", () => {
  const src = readFileSync(new URL("../src/my-invest.js", import.meta.url), "utf8");
  assert.match(src, /env\.MY_INVEST_GITHUB_TOKEN/);
  assert.equal(/env\.GITHUB_TOKEN/.test(src), false);
  assert.equal(/env\.KABU_NOTE_GITHUB_TOKEN/.test(src), false);
});
