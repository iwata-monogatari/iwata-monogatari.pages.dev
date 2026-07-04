#!/usr/bin/env node
// data/future-themes.json の未調査テーマから、DeepReach調査用プロンプトを /prompts/{id}.txt に生成する。
// 調査済み(research_done以降)になったテーマのプロンプトは自動で削除する。
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const THEMES_PATH = path.join(ROOT, 'data', 'future-themes.json');
const PROMPTS_DIR = path.join(ROOT, 'prompts');

const AREA_NAME = {
  mitsuke: '見付', nakaizumi: '中泉', mikuriya: '御厨', toyoda: '豊田',
  nanbu: '南部', koyo: '向陽', ryuyo: '竜洋', fukude: '福田', toyooka: '豊岡', common: '磐田共通',
};

// このステータスの間だけ、DeepReachへ投げるプロンプトが必要
const NEEDS_PROMPT_STATUS = new Set(['planned', 'research_queued', 'researching']);

function buildPrompt(theme) {
  const primaryName = AREA_NAME[theme.primary_area] || theme.primary_area;
  const relatedNames = (theme.related_areas || [])
    .map((a) => AREA_NAME[a] || a)
    .join('、');

  return `あなたは、静岡県磐田市の地域史・郷土史・交通史・地名史を調査するリサーチャーです。

以下のテーマについて、磐田物語の記事化を前提に、一次資料・自治体資料・図書館資料・文化財資料・郷土史資料・現地確認に役立つ情報を整理してください。

テーマID：${theme.id}
テーマ名：${theme.title}
主地区：${primaryName}
関連地区：${relatedNames}
分野：${theme.category}

調査条件：
- 丸写し禁止。記事化時は必ず再構成する前提で、事実関係を整理する。
- 史実、伝承、推測を分ける。
- 年代、地名、人物名、出典を明確にする。
- 磐田市の現代地名と対応できるようにする。
- 既存の磐田物語記事と重複しそうな論点を指摘する。
- 可能であれば、現地で確認すべき場所を列挙する。
- 関連する画像、古地図、碑、石造物、現存遺構があれば候補を挙げる。
- SEO上有効な検索語を自然に抽出する。

出力形式：
1. 概要
2. 重要な史実
3. 伝承・異説
4. 現代地図上の対応地点
5. 現地確認ポイント
6. 参考資料・URL
7. 記事化するときの章立て案
8. 既存記事との重複注意
9. 追加調査が必要な点
`;
}

function main() {
  const themes = JSON.parse(fs.readFileSync(THEMES_PATH, 'utf8'));

  fs.mkdirSync(PROMPTS_DIR, { recursive: true });

  const needed = themes.filter((t) => NEEDS_PROMPT_STATUS.has(t.deepreach_status));
  const neededIds = new Set(needed.map((t) => t.id));

  let written = 0;
  for (const theme of needed) {
    const filePath = path.join(PROMPTS_DIR, `${theme.id}.txt`);
    fs.writeFileSync(filePath, buildPrompt(theme), 'utf8');
    written += 1;
  }

  let removed = 0;
  for (const name of fs.readdirSync(PROMPTS_DIR)) {
    if (!name.endsWith('.txt')) continue;
    const id = name.replace(/\.txt$/, '');
    if (!neededIds.has(id)) {
      fs.unlinkSync(path.join(PROMPTS_DIR, name));
      removed += 1;
    }
  }

  console.log(`create-deepreach-prompts: ${written} prompts written, ${removed} stale prompts removed (${themes.length} themes total).`);
}

main();
