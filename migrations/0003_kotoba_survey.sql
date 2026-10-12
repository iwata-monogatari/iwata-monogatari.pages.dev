-- 磐田ことば調査（遠州弁辞典 /c006 の語ごとの「使う／聞いたことがある／知らない」）
-- 適用: wrangler d1 execute iwata_monogatari_bbs --remote --file migrations/0003_kotoba_survey.sql
-- functions/api/kotoba/_lib.js の ensureTables が初回リクエストで同じ定義を作るため、手動適用は必須ではない。

-- 1端末（visitor_id）につき1語1回答。答え直しは上書きする。
-- 氏名・連絡先は持たない。地区・世代は回答者の自己申告で、集計にだけ使う。
CREATE TABLE IF NOT EXISTS kotoba_survey (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  word_id     TEXT NOT NULL,
  answer      TEXT NOT NULL CHECK (answer IN ('use','heard','unknown')),
  district    TEXT NOT NULL DEFAULT 'none',
  generation  TEXT NOT NULL DEFAULT 'none',
  visitor_id  TEXT NOT NULL,
  ip_hash     TEXT,
  internal    INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL,
  UNIQUE (word_id, visitor_id)
);
CREATE INDEX IF NOT EXISTS idx_kotoba_survey_word ON kotoba_survey (word_id);
CREATE INDEX IF NOT EXISTS idx_kotoba_survey_ip ON kotoba_survey (ip_hash, updated_at);
