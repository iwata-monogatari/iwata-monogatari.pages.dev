-- 磐田物語 みんなの掲示板 / Cloudflare D1 スキーマ
-- 適用例:
--   wrangler d1 execute iwata_monogatari_bbs --file=./schema-bbs.sql
--   wrangler d1 execute iwata_monogatari_bbs --remote --file=./schema-bbs.sql

CREATE TABLE IF NOT EXISTS bbs_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL DEFAULT '匿名',
  area TEXT,
  body TEXT NOT NULL,
  related_url TEXT,
  status TEXT NOT NULL DEFAULT 'published',
  ip_hash TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  deleted_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_bbs_posts_status_created
ON bbs_posts(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_bbs_posts_created
ON bbs_posts(created_at DESC);

-- 連続投稿チェック用（同一 ip_hash の直近投稿を高速に引く）
CREATE INDEX IF NOT EXISTS idx_bbs_posts_iphash_created
ON bbs_posts(ip_hash, created_at DESC);
