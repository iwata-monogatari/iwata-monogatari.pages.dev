import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { onRequestPost, onRequestGet, ORIGIN } from '../functions/api/reactions/cheshire.js';
import { onRequest as cors } from '../functions/api/reactions/_middleware.js';

const endpoint = 'https://iwata-monogatari.net/api/reactions/cheshire';
test('三問別に一票を保持し、再送・古い回答・内部確認を読者票に重ねない', async () => {
  const sqlite = new DatabaseSync(':memory:');
  const db = {
    prepare(sql) {
      let params = [];
      return {
        bind(...values) { params = values; return this; },
        run() { return sqlite.prepare(sql).run(...params); },
        all() { return {results:sqlite.prepare(sql).all(...params)}; }
      };
    },
    batch: async statements => statements.map(s => s.run())
  };
  const env = {DB:db};
  const get = async () => (await onRequestGet({env,request:new Request(endpoint+'?days=7')})).json();
  const send = (changes={},origin=ORIGIN) => onRequestPost({env,request:new Request(endpoint,{
    method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},
    body:JSON.stringify({vid:'0123456789abcdef',question:'purr',choice:'same',internal:false,revision:1,...changes})
  })});
  try {
    assert.deepEqual((await get()).items.map(q=>q.total),[0,0,0]);
    assert.equal((await send()).status,200);
    await send({choice:'different',revision:2});
    await send({choice:'same'});
    await send({choice:'different',revision:2});
    await send({vid:'fedcba9876543210',internal:true});
    await send({question:'paths',choice:'ask'});
    await send({question:'grin',choice:'shape'});
    assert.equal((await send({choice:'ask'})).status,400);
    assert.equal((await send({},'https://other.example')).status,403);
    const {items}=await get();
    assert.deepEqual(items.map(q=>q.total),[1,1,1]);
    assert.deepEqual(items[0].answers.map(a=>a.count),[0,1,0]);
    sqlite.exec("UPDATE cheshire_dialogue_answers SET updated_at='2000-01-01' WHERE question='grin'");
    assert.deepEqual((await get()).items.map(q=>q.total),[1,1,0]);
  } finally { sqlite.close(); }
});
test('回答先だけにチェシャ猫からのCORSを許可する', async () => {
  const preflight = path => cors({request:new Request('https://iwata-monogatari.net'+path,{method:'OPTIONS',headers:{Origin:ORIGIN}})});
  assert.equal((await preflight('/api/reactions/cheshire')).headers.get('Access-Control-Allow-Origin'),ORIGIN);
  assert.equal((await preflight('/api/reactions/admin-summary')).status,403);
  assert.equal((await preflight('/api/reactions/react')).status,403);
});
