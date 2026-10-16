import { json, readJson, storedPath, normalizePath, validVisitorId, REACTIONS, sanitizeText, nowIso } from "./_lib.js";
import { ensureFeedbackTables, FEEDBACK_PATH, FEEDBACK_QUESTION, FEEDBACK_VERSION, FEEDBACK_UI, FORMATS } from "./_feedback.js";

export async function onRequestPost({ request, env }) {
  if (!env.DB) return json({ ok: false, error: "データベース未設定です。" }, 503);
  const body = await readJson(request);
  if (!body || typeof body !== "object" || Array.isArray(body)) return json({ ok: false, error: "不正なリクエストです。" }, 400);
  const path = storedPath(body, request);
  if (body.site !== "oishi" || !path || normalizePath(body.path) !== FEEDBACK_PATH ||
      body.question !== FEEDBACK_QUESTION || body.version !== FEEDBACK_VERSION || body.ui !== FEEDBACK_UI ||
      body.articleType !== "event" || !["mobile", "desktop"].includes(body.device) ||
      !["react", "format"].includes(body.action) || !REACTIONS.includes(body.reaction) ||
      !validVisitorId(body.vid) || !validVisitorId(body.sid) ||
      !Number.isSafeInteger(body.revision) || body.revision < 1 ||
      (body.action === "format" && !FORMATS.includes(body.format))) {
    return json({ ok: false, error: "不正なリクエストです。" }, 400);
  }
  const db = env.DB;
  try {
    await ensureFeedbackTables(db);
    if (body.action === "format") {
      const previous = await db.prepare("SELECT reaction FROM article_reactions WHERE path = ?1 AND visitor_id = ?2").bind(path, body.vid).first();
      if (!previous) return json({ ok: false, error: "先に記事への反応を選んでください。" }, 409);
    }
    const now = nowIso();
    const title = sanitizeText(body.title || "", 200);
    const internal = body.internal === true ? 1 : 0;
    const reactionAt = body.action === "react" ? now : null;
    const preference = body.action === "format" ? body.format : null;
    const statements = [db.prepare(`INSERT INTO article_feedback_answers
      (path, visitor_id, session_id, question_id, question_version, ui_version, article_type,
       device, title, reaction, reaction_at, preference, preference_at, revision, internal, created_at, updated_at)
      VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16, ?16)
      ON CONFLICT (path, visitor_id, session_id, question_id, question_version) DO UPDATE SET
        reaction = excluded.reaction,
        reaction_at = COALESCE(excluded.reaction_at, article_feedback_answers.reaction_at),
        preference = COALESCE(excluded.preference, article_feedback_answers.preference),
        preference_at = COALESCE(excluded.preference_at, article_feedback_answers.preference_at),
        revision = excluded.revision, internal = excluded.internal, device = excluded.device,
        title = excluded.title, ui_version = excluded.ui_version, updated_at = excluded.updated_at
      WHERE excluded.revision > article_feedback_answers.revision`)
      .bind(path, body.vid, body.sid, body.question, body.version, body.ui, body.articleType,
        body.device, title, body.reaction, reactionAt, preference, preference ? now : null, body.revision, internal, now)];
    if (body.action === "react") {
      // The existing dashboards keep their one-browser/one-article totals.
      // A delayed retry may not overwrite a later answer from the same session.
      statements.push(db.prepare(`INSERT INTO article_reactions
        (path, title, reaction, visitor_id, internal, created_at, updated_at)
        SELECT path, title, reaction, visitor_id, internal, ?1, ?1 FROM article_feedback_answers
        WHERE path = ?2 AND visitor_id = ?3 AND session_id = ?4 AND question_id = ?5
          AND question_version = ?6 AND revision = ?7
        ON CONFLICT (path, visitor_id) DO UPDATE SET reaction = excluded.reaction,
          title = excluded.title, internal = excluded.internal, updated_at = excluded.updated_at`)
        .bind(now, path, body.vid, body.sid, body.question, body.version, body.revision));
    }
    await db.batch(statements);
    const stored = await db.prepare(`SELECT revision FROM article_feedback_answers
      WHERE path = ?1 AND visitor_id = ?2 AND session_id = ?3 AND question_id = ?4 AND question_version = ?5`)
      .bind(path, body.vid, body.sid, body.question, body.version).first();
    return json({ ok: true, revision: stored.revision });
  } catch (error) {
    console.error("article-feedback-save-failed", error && error.message);
    return json({ ok: false, error: "保存に失敗しました。もう一度お試しください。" }, 500);
  }
}
