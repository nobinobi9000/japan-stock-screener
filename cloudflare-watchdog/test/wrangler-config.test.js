// C9: wrangler.toml の静的検査（TOMLパーサに依存しない簡易検査）
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const toml = readFileSync(new URL("../wrangler.toml", import.meta.url), "utf8");
const m = toml.match(/^crons\s*=\s*\[(.*?)\]/ms);
const crons = [...m[1].matchAll(/"([^"]+)"/g)].map((x) => x[1]);

test("C9 既存3 cron は不変で、合計4本", () => {
  assert.deepEqual(crons.slice(0, 3), ["30 7 * * 2-6", "30 9 * * 2-6", "0 11 * * 2-6"]);
  assert.equal(crons.length, 4);
});

test("C9 追加 cron: 5フィールドで JST 月〜金 16:00〜20:55 の5分刻み", () => {
  const f = crons[3].split(/\s+/);
  assert.equal(f.length, 5);
  assert.deepEqual(f, ["*/5", "7-11", "*", "*", "2-6"]);
  const [h0, h1] = f[1].split("-").map(Number);
  const times = [];
  for (let h = h0; h <= h1; h++) for (let mi = 0; mi < 60; mi += 5) times.push((h + 9) * 60 + mi);
  assert.equal(times.length, 60);
  assert.equal(times[0], 16 * 60);
  assert.equal(times.at(-1), 20 * 60 + 55);
  assert.ok(times.includes(16 * 60 + 45) && times.includes(19 * 60 + 55) && times.includes(20 * 60 + 5));
});

test("C9 vars に秘密様の値が無く、workers_dev=false のまま", () => {
  const vars = toml.slice(toml.indexOf("[vars]"));
  const values = [...vars.matchAll(/^[A-Z_]+\s*=\s*"([^"]*)"/gm)].map((x) => x[1]);
  for (const v of values) for (const bad of ["github_pat_", "ghp_", "re_", "eyJ"]) assert.equal(v.includes(bad), false);
  assert.match(toml, /^workers_dev\s*=\s*false/m);
  assert.match(toml, /^KABU_NOTE_DRY_RUN\s*=\s*"false"/m);
  assert.match(toml, /^\[observability\]\s*\r?\nenabled\s*=\s*true/m);
});
