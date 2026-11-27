import { json, nowIso, readJson, validVisitorId } from './_lib.js';
import { feedbackPeriod } from './_feedback.js';

export const ORIGIN = 'https://cheshire.atawi.link';
const questions = [
  {id:'purr', title:'猫のゴロゴロは、犬のうなり声と同じ？', answers:{same:'同じだと思う', different:'違うと思う', unsure:'音だけでは決められない'}},
  {id:'paths', title:'行き先は決めてない。でも、暗い道は嫌。', answers:{light:'明るい道をすすめる', ask:'何が嫌なのかを聞く', either:'それでも、どちらでもいい'}},
  {id:'grin', title:'笑いだけで、なぜ「あの猫」だとわかる？', answers:{shape:'笑いの形でわかる', sequence:'消えるところを見たから', undecided:'笑いだけではわからない'}}
];

const schema = `CREATE TABLE IF NOT EXISTS cheshire_dialogue_answers (
  question TEXT NOT NULL, visitor_id TEXT NOT NULL, choice TEXT NOT NULL,
  internal INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL, revision INTEGER NOT NULL,
  PRIMARY KEY (question, visitor_id))`;
const prepared = new WeakMap();
async function setup(db) {
  if (!prepared.has(db)) prepared.set(db, db.batch([
    db.prepare(schema), db.prepare('CREATE INDEX IF NOT EXISTS idx_cheshire_dialogue_period ON cheshire_dialogue_answers(internal, updated_at)')
  ]).catch(error => { prepared.delete(db); throw error; }));
  return prepared.get(db);
}
export async function onRequestPost({request,env}) {
  if (request.headers.get('Origin') !== ORIGIN) return json({ok:false},403);
  if (!request.headers.get('Content-Type')?.startsWith('application/json')) return json({ok:false},415);
  const b = await readJson(request);
  const question = questions.find(q => q.id === b?.question);
  if (!question || typeof b.choice !== 'string' || !Object.hasOwn(question.answers,b.choice)
      || !validVisitorId(b.vid) || typeof b.internal !== 'boolean' || !Number.isSafeInteger(b.revision) || b.revision < 1) return json({ok:false},400);
  try {
    await setup(env.DB);
    await env.DB.prepare(`INSERT INTO cheshire_dialogue_answers(question,visitor_id,choice,internal,updated_at,revision)
      VALUES(?,?,?,?,?,?) ON CONFLICT(question,visitor_id) DO UPDATE SET
      choice=excluded.choice, internal=excluded.internal, updated_at=excluded.updated_at, revision=excluded.revision
      WHERE excluded.revision > cheshire_dialogue_answers.revision`)
      .bind(question.id,b.vid,b.choice,Number(b.internal),nowIso(),b.revision).run();
    return json({ok:true});
  } catch { return json({ok:false,error:'回答を保存できませんでした。'},503); }
}
export async function onRequestGet({request,env}) {
  const {since,days}=feedbackPeriod(new URL(request.url).searchParams);
  try {
    await setup(env.DB);
    const {results}=await env.DB.prepare(`SELECT question, choice, COUNT(*) AS n FROM cheshire_dialogue_answers
      WHERE internal=0 AND updated_at>=? GROUP BY question,choice`).bind(since).all();
    const items=questions.map(q => {
      const answers=Object.entries(q.answers).map(([id,label])=>({
        id,label,count:Number(results.find(r=>r.question===q.id && r.choice===id)?.n || 0)
      }));
      return {id:q.id,title:q.title,answers,total:answers.reduce((n,a)=>n+a.count,0)};
    });
    return json({ok:true,days,items});
  } catch { return json({ok:false,error:'回答を集計できませんでした。'},503); }
}
