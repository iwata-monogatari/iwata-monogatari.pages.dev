import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { onRequestPost as save } from "../functions/api/reactions/feedback.js";
import { onRequestGet as summary } from "../functions/api/reactions/admin-feedback.js";
import { onRequest as cors } from "../functions/api/reactions/_middleware.js";

function fixture() {
  const sqlite = new DatabaseSync(":memory:");
  for (const name of ["0002_article_reactions.sql", "0004_article_feedback.sql"]) {
    sqlite.exec(readFileSync(new URL("../migrations/" + name, import.meta.url), "utf8"));
  }
  const DB = {
    prepare(sql) {
      const indexes = [];
      const statement = sqlite.prepare(sql.replace(/\?(\d+)/g, (_, n) => { indexes.push(Number(n) - 1); return "?"; }));
      let values = [];
      return {
        bind(...args) { values = args; return this; },
        async run() { return statement.run(...indexes.map(i => values[i])); },
        async first() { return statement.get(...indexes.map(i => values[i])) || null; },
        async all() { return { results: statement.all(...indexes.map(i => values[i])) }; },
      };
    },
    async batch(statements) {
      sqlite.exec("BEGIN");
      try { const results = []; for (const s of statements) results.push(await s.run()); sqlite.exec("COMMIT"); return results; }
      catch (error) { sqlite.exec("ROLLBACK"); throw error; }
    },
  };
  const env = { DB, BBS_ADMIN_TOKEN: "test-only-token" };
  const base = { site: "oishi", path: "/articles/iwata-oishihiroyuki0524", title: "テスト記事", vid: "0123456789abcdef01234567",
    sid: "abcdef012345678901234567", revision: 1, action: "react", reaction: "learned", question: "participation-flow",
    version: "1", ui: "20261016-1", articleType: "event", device: "mobile", internal: false };
  const post = (changes = {}, origin = "https://oishi-hiroyuki.org") => save({ env, request: new Request("https://iwata-monogatari.net/api/reactions/feedback", {
    method: "POST", headers: { "Content-Type": "application/json", Origin: origin }, body: JSON.stringify({ ...base, ...changes }),
  }) });
  const get = (query = "", authorized = true) => summary({ env, request: new Request("https://iwata-monogatari.net/api/reactions/admin-feedback" + query,
    { headers: authorized ? { Authorization: "Bearer test-only-token" } : {} }) });
  return { sqlite, env, base, post, get };
}

test("positive reactions, retries, changed choices and stale requests keep one answer", async () => {
  const { sqlite, post } = fixture();
  try {
    assert.equal((await post()).status, 200);
    assert.equal((await post()).status, 200);
    assert.equal((await post({ reaction: "more", revision: 3 })).status, 200);
    const late = await (await post({ reaction: "local", revision: 2 })).json();
    assert.equal(late.revision, 3);
    assert.equal(sqlite.prepare("SELECT COUNT(*) AS n FROM article_feedback_answers").get().n, 1);
    assert.equal(sqlite.prepare("SELECT reaction FROM article_reactions").get().reaction, "more");
  } finally { sqlite.close(); }
});

test("all three positive reactions allow an optional format, and changing it does not add votes", async () => {
  const { sqlite, post, get } = fixture();
  try {
    for (const [index, reaction] of ["learned", "local", "more"].entries()) {
      const vid = "a".repeat(23) + index;
      assert.equal((await post({ vid, reaction })).status, 200);
      assert.equal((await post({ vid, reaction, action: "format", format: "diagram", revision: 2 })).status, 200);
      assert.equal((await post({ vid, reaction, action: "format", format: "qa", revision: 3 })).status, 200);
    }
    const data = await (await get()).json();
    assert.equal(data.rows[0].reactions, 3);
    assert.equal(data.rows[0].answers, 3);
    assert.equal(data.rows[0].qa, 3);
    assert.equal(data.rows[0].diagram, 0);
    assert.doesNotMatch(JSON.stringify(data), /visitor_id|session_id|ip_hash|0123456789abcdef/);
  } finally { sqlite.close(); }
});

test("a returning browser's format answer does not manufacture a new primary reaction", async () => {
  const { sqlite, post, get } = fixture();
  try {
    await post();
    await post({ sid: "b".repeat(24), action: "format", format: "list" });
    const data = await (await get()).json();
    assert.equal(data.rows[0].reactions, 1);
    assert.equal(data.rows[0].answers, 1);
    assert.equal(sqlite.prepare("SELECT COUNT(*) AS n FROM article_reactions").get().n, 1);
  } finally { sqlite.close(); }
});

test("reject unsupported articles, negative options, unknown versions and foreign origins", async () => {
  const { sqlite, post } = fixture();
  try {
    for (const changes of [{ path: "/articles/iwata-oishihiroyuki0525" }, { reaction: "unclear" }, { version: "2" },
      { action: "format", format: "uninterested" }, { revision: -1 }, { sid: "short" }, { site: "iwata" }]) {
      assert.equal((await post(changes)).status, 400);
    }
    assert.equal((await post({}, "https://example.com")).status, 400);
    assert.equal(sqlite.prepare("SELECT COUNT(*) AS n FROM article_feedback_answers").get().n, 0);
  } finally { sqlite.close(); }
});

test("format requires a saved reaction; administrators and internal traffic stay separate", async () => {
  const { sqlite, post, get } = fixture();
  try {
    assert.equal((await post({ action: "format", format: "qa" })).status, 409);
    await post({ internal: true });
    await post({ action: "format", format: "qa", revision: 2, internal: true });
    assert.equal((await get("", false)).status, 401);
    assert.equal((await (await get()).json()).rows.length, 0);
    assert.equal((await (await get("?internal=1")).json()).rows[0].qa, 1);
    assert.equal((await (await get("?site=iwata&internal=1")).json()).rows.length, 0);
    assert.equal((await get("?site=unknown")).status, 400);
  } finally { sqlite.close(); }
});

test("cross-origin partner writes work, while the new administrator endpoint has no CORS access", async () => {
  const make = path => ({ request: new Request("https://iwata-monogatari.net/api/reactions/" + path, {
    method: "OPTIONS", headers: { Origin: "https://oishi-hiroyuki.org" },
  }), next: () => new Response("ok") });
  assert.equal((await cors(make("feedback"))).status, 204);
  assert.equal((await cors(make("admin-feedback"))).status, 403);
});
