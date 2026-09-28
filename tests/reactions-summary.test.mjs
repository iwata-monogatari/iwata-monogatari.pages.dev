import assert from "node:assert/strict";
import test from "node:test";
import { DatabaseSync } from "node:sqlite";
import { onRequestGet as summary } from "../functions/api/reactions/summary.js";
import { onRequestGet as admin } from "../functions/api/reactions/admin-summary.js";
import { onRequestGet as counts } from "../functions/api/reactions/counts.js";
import { readFileSync } from "node:fs";

function fixture() {
  const sqlite = new DatabaseSync(":memory:");
  sqlite.exec(readFileSync(new URL("../migrations/0002_article_reactions.sql", import.meta.url), "utf8"));
  const DB = {
    prepare(sql) {
      let values = [];
      const args = [];
      const statement = sqlite.prepare(sql.replace(/\?(\d+)/g, (_, n) => { args.push(Number(n) - 1); return "?"; }));
      return {
        bind(...v) { values = v; return this; },
        async all() { return { results: statement.all(...args.map(i => values[i])) }; },
        async first() { return statement.get(...args.map(i => values[i])); },
        async run() { return statement.run(...args.map(i => values[i])); },
      };
    },
    async batch(statements) { return Promise.all(statements.map(s => s.run())); },
  };
  const now = new Date().toISOString();
  const insert = sqlite.prepare("INSERT INTO article_reactions(path,title,reaction,visitor_id,ip_hash,internal,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)");
  insert.run("/article-a", "磐田のテスト記事", "learned", "private-visitor-a", "private-ip", 0, now, now);
  insert.run("/article-a", "磐田のテスト記事", "more", "private-visitor-b", "private-ip", 0, now, now);
  insert.run("/internal", "管理者の確認", "local", "private-internal", "private-ip", 1, now, now);
  insert.run("https://oishi-hiroyuki.org/article-b", "大石のテスト記事", "local", "private-visitor-c", "private-ip", 0, now, now);
  insert.run("/old", "古い記事", "local", "private-visitor-d", "private-ip", 0, "2020-01-01T00:00:00Z", "2020-01-01T00:00:00Z");
  const note = sqlite.prepare("INSERT INTO article_reaction_notes(path,title,note,visitor_id,ip_hash,internal,created_at) VALUES(?,?,?,?,?,?,?)");
  note.run("/article-a", "磐田のテスト記事", "秘密の一言", "private-note-visitor", "private-note-ip", 0, now);
  note.run("/internal", "管理者", "管理者の一言", "private-admin", "private-ip", 1, now);
  const env = { DB, BBS_ADMIN_TOKEN: "test-only-token" };
  return { sqlite, env, insert };
}
function request(query = "") { return new Request("https://iwata-monogatari.net/api/reactions/summary" + query); }

test("without a token, return reaction aggregates and never private notes or identifiers", async () => {
  const { sqlite, env } = fixture();
  try {
    const response = await summary({ request: request("?site=iwata&days=7&internal=1"), env });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("cache-control"), "no-store");
    const result = await response.json();
    assert.deepEqual(result.totals, { reactions: 2, learned: 1, local: 0, more: 1, notes: 1 });
    assert.equal(result.pages.length, 1);
    assert.equal(result.pages[0].path, "/article-a");
    assert.equal(result.daily[0].day, new Date(Date.now() + 9 * 3600000).toISOString().slice(0, 10));
    assert.equal("notes" in result, false);
    assert.equal("visitors" in result.totals, false);
    assert.doesNotMatch(JSON.stringify(result), /秘密|private-|visitor_id|ip_hash|管理者/);
    const c = await (await counts({ env })).json();
    assert.equal(result.totals.reactions, c.sites.iwata.week);
    assert.equal(result.totals.notes, c.sites.iwata.notes_week);
  } finally { sqlite.close(); }
});

test("site selection, all sites, all time, and invalid site handling", async () => {
  const { sqlite, env } = fixture();
  try {
    const oishi = await (await summary({ request: request("?site=oishi"), env })).json();
    assert.equal(oishi.totals.reactions, 1);
    assert.equal(oishi.pages[0].local, 1);
    assert.equal(oishi.totals.notes, 0);
    const all = await (await summary({ request: request("?site=all&days=0"), env })).json();
    assert.equal(all.totals.reactions, 4);
    assert.equal(all.pages.length, 3);
    assert.equal((await summary({ request: request("?site=unknown"), env })).status, 400);
  } finally { sqlite.close(); }
});

test("7 days use Japanese calendar boundaries, matching dashboard counts", async () => {
  const { sqlite, env, insert } = fixture();
  try {
    const today = new Date(Date.now() + 9 * 3600000).toISOString().slice(0, 10);
    const start = Date.parse(today + "T00:00:00+09:00") - 6 * 86400000;
    for (const [path, time] of [["/boundary", start], ["/outside", start - 1]]) {
      const timestamp = new Date(time).toISOString();
      insert.run(path, path, "learned", path, "hash", 0, timestamp, timestamp);
    }
    const result = await (await summary({ request: request("?days=7"), env })).json();
    assert.ok(result.pages.some(p => p.path === "/boundary"));
    assert.ok(!result.pages.some(p => p.path === "/outside"));
    const c = await (await counts({ env })).json();
    assert.equal(result.totals.reactions, c.sites.iwata.week);
  } finally { sqlite.close(); }
});

test("private notes still require the administrator token", async () => {
  const { sqlite, env } = fixture();
  try {
    assert.equal((await admin({ request: request(), env })).status, 401);
    const authorized = new Request("https://iwata-monogatari.net/api/reactions/admin-summary", { headers: { Authorization: "Bearer test-only-token" } });
    const result = await (await admin({ request: authorized, env })).json();
    assert.equal(result.notes.length, 1);
    assert.equal(result.notes[0].note, "秘密の一言");
  } finally { sqlite.close(); }
});

test("missing database returns an error, not misleading zero counts", async () => {
  const response = await summary({ request: request(), env: {} });
  assert.equal(response.status, 500);
  assert.equal((await response.json()).ok, false);
});
