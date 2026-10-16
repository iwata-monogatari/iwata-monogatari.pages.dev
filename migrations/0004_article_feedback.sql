-- Selected, positive answers only. Passive view events stay in GA4, not D1 counters.
CREATE TABLE IF NOT EXISTS article_feedback_answers (
  path TEXT NOT NULL,
  visitor_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  question_version TEXT NOT NULL,
  ui_version TEXT NOT NULL,
  article_type TEXT NOT NULL,
  device TEXT NOT NULL CHECK (device IN ('mobile','desktop')),
  title TEXT NOT NULL DEFAULT '',
  reaction TEXT NOT NULL CHECK (reaction IN ('learned','local','more')),
  reaction_at TEXT,
  preference TEXT CHECK (preference IN ('list','diagram','qa')),
  preference_at TEXT,
  revision INTEGER NOT NULL,
  internal INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (path, visitor_id, session_id, question_id, question_version)
);
CREATE INDEX IF NOT EXISTS idx_article_feedback_updated ON article_feedback_answers (updated_at);
