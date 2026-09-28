-- 記事末尾の反応ボタン（3種）と、押したあとの非公開の一言
-- 適用: wrangler d1 execute iwata_monogatari_bbs --remote --file migrations/0002_article_reactions.sql

-- 1端末（visitor_id）につき1記事1票。押し直しは reaction を上書きする。
CREATE TABLE IF NOT EXISTS article_reactions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  path        TEXT NOT NULL,
  title       TEXT,
  reaction    TEXT NOT NULL CHECK (reaction IN ('learned','local','more')),
  visitor_id  TEXT NOT NULL,
  ip_hash     TEXT,
  internal    INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL,
  UNIQUE (path, visitor_id)
);
CREATE INDEX IF NOT EXISTS idx_article_reactions_path ON article_reactions (path);
CREATE INDEX IF NOT EXISTS idx_article_reactions_created ON article_reactions (created_at);

-- 一言は公開しない。管理画面でのみ読む。
CREATE TABLE IF NOT EXISTS article_reaction_notes (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  path        TEXT NOT NULL,
  title       TEXT,
  reaction    TEXT,
  note        TEXT NOT NULL,
  visitor_id  TEXT NOT NULL,
  ip_hash     TEXT,
  internal    INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_article_reaction_notes_created ON article_reaction_notes (created_at);
CREATE INDEX IF NOT EXISTS idx_article_reaction_notes_ip ON article_reaction_notes (ip_hash, created_at);
