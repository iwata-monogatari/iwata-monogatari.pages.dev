#!/usr/bin/env node
// data/future-themes.json の整合性チェック（CI・手動どちらからでも実行可）。
'use strict';

const fs = require('fs');
const path = require('path');

const THEMES_PATH = path.join(__dirname, '..', 'data', 'future-themes.json');

const VALID_AREAS = new Set([
  'mitsuke', 'nakaizumi', 'mikuriya', 'toyoda', 'nanbu',
  'koyo', 'ryuyo', 'fukude', 'toyooka', 'common',
]);
const VALID_PRIORITY = new Set(['A', 'B', 'C']);
const VALID_DEEPREACH_STATUS = new Set([
  'planned', 'research_queued', 'researching', 'research_done',
  'outline_done', 'html_draft', 'reviewing', 'published', 'hold', 'merged',
]);
const REQUIRED_FIELDS = [
  'id', 'title', 'primary_area', 'related_areas', 'category', 'priority',
  'deepreach_status', 'article_status', 'updated_at',
];

function main() {
  const errors = [];
  const raw = fs.readFileSync(THEMES_PATH, 'utf8');

  let themes;
  try {
    themes = JSON.parse(raw);
  } catch (e) {
    console.error(`validate-future-themes: JSONとして読み込めません: ${e.message}`);
    process.exit(1);
  }

  if (!Array.isArray(themes)) {
    console.error('validate-future-themes: トップレベルは配列である必要があります。');
    process.exit(1);
  }

  const seenIds = new Set();

  themes.forEach((t, i) => {
    const where = `#${i} (${t && t.id ? t.id : '?'})`;

    for (const field of REQUIRED_FIELDS) {
      if (t[field] === undefined || t[field] === null || t[field] === '') {
        errors.push(`${where}: 必須フィールド "${field}" がありません`);
      }
    }
    if (!t.id) return;

    if (!/^T\d{3,}$/.test(t.id)) {
      errors.push(`${where}: id "${t.id}" は T001 形式ではありません`);
    }
    if (seenIds.has(t.id)) {
      errors.push(`${where}: id "${t.id}" が重複しています`);
    }
    seenIds.add(t.id);

    if (t.primary_area && !VALID_AREAS.has(t.primary_area)) {
      errors.push(`${where}: primary_area "${t.primary_area}" は未知の地区slugです`);
    }
    if (Array.isArray(t.related_areas)) {
      for (const a of t.related_areas) {
        if (!VALID_AREAS.has(a)) {
          errors.push(`${where}: related_areas に未知の地区slug "${a}"`);
        }
      }
    } else {
      errors.push(`${where}: related_areas は配列である必要があります`);
    }

    if (t.priority && !VALID_PRIORITY.has(t.priority)) {
      errors.push(`${where}: priority "${t.priority}" はA/B/Cのいずれかである必要があります`);
    }
    if (t.deepreach_status && !VALID_DEEPREACH_STATUS.has(t.deepreach_status)) {
      errors.push(`${where}: deepreach_status "${t.deepreach_status}" は未知のステータスです`);
    }
  });

  if (errors.length) {
    console.error(`validate-future-themes: ${errors.length}件のエラー\n` + errors.map((e) => ` - ${e}`).join('\n'));
    process.exit(1);
  }

  console.log(`validate-future-themes: OK (${themes.length}テーマ、エラーなし)`);
}

main();
