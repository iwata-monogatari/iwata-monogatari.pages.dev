import { ensureTables } from "./_lib.js";

export const FEEDBACK_PATH = "/articles/iwata-oishihiroyuki0524";
export const FEEDBACK_QUESTION = "participation-flow";
export const FEEDBACK_VERSION = "1";
export const FEEDBACK_UI = "20261016-1";
export const FORMATS = ["list", "diagram", "qa"];
const ready = new WeakMap();

export async function ensureFeedbackTables(db) {
  if (!ready.has(db)) {
    ready.set(db, (async () => {
      await ensureTables(db);
      await db.batch([
        db.prepare(`CREATE TABLE IF NOT EXISTS article_feedback_answers (
          path TEXT NOT NULL, visitor_id TEXT NOT NULL, session_id TEXT NOT NULL,
          question_id TEXT NOT NULL, question_version TEXT NOT NULL, ui_version TEXT NOT NULL,
          article_type TEXT NOT NULL, device TEXT NOT NULL CHECK (device IN ('mobile','desktop')),
          title TEXT NOT NULL DEFAULT '', reaction TEXT NOT NULL CHECK (reaction IN ('learned','local','more')),
          reaction_at TEXT, preference TEXT CHECK (preference IN ('list','diagram','qa')), preference_at TEXT,
          revision INTEGER NOT NULL, internal INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          PRIMARY KEY (path, visitor_id, session_id, question_id, question_version))`),
        db.prepare("CREATE INDEX IF NOT EXISTS idx_article_feedback_updated ON article_feedback_answers (updated_at)"),
      ]);
    })().catch(error => { ready.delete(db); throw error; }));
  }
  return ready.get(db);
}

export function feedbackPeriod(searchParams) {
  const requested = Number(searchParams.get("days") ?? "30");
  const days = [0, 7, 30, 90].includes(requested) ? requested : 30;
  const today = new Date(Date.now() + 9 * 3600000).toISOString().slice(0, 10);
  const since = days ? new Date(Date.parse(today + "T00:00:00+09:00") - (days - 1) * 86400000).toISOString() : "0000";
  return { days, today, since };
}
