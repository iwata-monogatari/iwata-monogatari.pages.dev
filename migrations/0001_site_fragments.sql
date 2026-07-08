CREATE TABLE IF NOT EXISTS site_fragments (
  fragment_key TEXT PRIMARY KEY,
  html TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_site_fragments_active
  ON site_fragments (is_active);
