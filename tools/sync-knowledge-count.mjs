#!/usr/bin/env node
// 磐田の集合知（公開記事数）を data/pages.json から算出し、表示先ファイルへ反映する。
// 使い方:
//   node tools/sync-knowledge-count.mjs           反映 + 監査レポート表示
//   node tools/sync-knowledge-count.mjs --check   反映せず、ズレがあれば exit code 1（CI向け）
//   node tools/sync-knowledge-count.mjs --audit   反映せず、監査レポートのみ表示

import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PAGES_JSON = path.join(ROOT, "data", "pages.json");
const ARTICLE_INDEX = path.join(ROOT, "c034.html");

// data-knowledge-count 属性を持つ要素の数字だけを書き換える。
// 対象ファイルを増やしたい場合はここに追記する（例: c033.html に表示を追加したら追加する）。
const DISPLAY_TARGETS = [path.join(ROOT, "index.html")];

const args = new Set(process.argv.slice(2));
const CHECK_MODE = args.has("--check");
const AUDIT_ONLY = args.has("--audit");

function fail(message) {
  console.error(`✗ ${message}`);
  process.exitCode = 1;
}

async function loadPagesJson() {
  const raw = await readFile(PAGES_JSON, "utf8");
  return JSON.parse(raw);
}

async function savePagesJson(data) {
  const text = JSON.stringify(data, null, 2) + "\n";
  await writeFile(PAGES_JSON, text, { encoding: "utf8" });
}

function countKnowledge(pages) {
  return pages.filter((p) => p.count_as_knowledge === true).length;
}

// 全記事一覧(c034.html)に実際に載っているユニークな記事リンクを、監査の突き合わせ元として使う。
// data/pages.json は登録漏れが起きやすいため（本スキルの既知の注意点）、
// 「一覧には載っているのに知識記事として数えられていない」ページを機械的に検出する。
async function auditAgainstArticleIndex(pages) {
  let html;
  try {
    html = await readFile(ARTICLE_INDEX, "utf8");
  } catch {
    return null; // c034.html が見つからない環境では監査をスキップする
  }
  const hrefs = [...html.matchAll(/<li><a href="([^"]+)">/g)].map((m) =>
    m[1].replace(/^\//, "")
  );
  const indexUrls = new Set(hrefs);

  const byUrl = new Map(pages.map((p) => [p.url, p]));

  const missing = []; // 一覧にあるが pages.json に存在しない
  const notCounted = []; // pages.json にはあるが count_as_knowledge が true でない
  const brokenLinks = []; // 一覧のリンク先ファイルが実在しない

  for (const url of indexUrls) {
    const pg = byUrl.get(url);
    if (!pg) {
      missing.push(url);
      const localPath = resolveLocalPath(url);
      try {
        await readFile(path.join(ROOT, localPath));
      } catch {
        brokenLinks.push(url);
      }
      continue;
    }
    if (pg.count_as_knowledge !== true) {
      notCounted.push({ url, status: pg.status ?? "(status未設定)" });
    }
  }

  const orphaned = pages
    .filter((p) => p.count_as_knowledge === true && !indexUrls.has(p.url))
    .map((p) => p.url);

  return { totalIndexed: indexUrls.size, missing, notCounted, orphaned, brokenLinks };
}

function resolveLocalPath(url) {
  let u = url.replace(/^\//, "");
  if (u === "" || u.endsWith("/")) return u + "index.html";
  if (!u.endsWith(".html")) return u + "/index.html";
  return u;
}

async function updateDisplayFile(filePath, count) {
  let text;
  try {
    text = await readFile(filePath, "utf8");
  } catch {
    return { path: filePath, changed: false, found: false };
  }

  const pattern = /(data-knowledge-count[^>]*>)\s*\d+\s*(<)/;
  if (!pattern.test(text)) {
    return { path: filePath, changed: false, found: false };
  }

  const before = text;
  text = text.replace(pattern, (_m, open, close) => `${open}${count}${close}`);
  const changed = text !== before;

  if (changed && !CHECK_MODE && !AUDIT_ONLY) {
    // CRLF化を防ぐため改行コードは明示的に LF を指定する（Windows環境での既知の事故）。
    await writeFile(filePath, text, { encoding: "utf8" });
  }
  return { path: filePath, changed, found: true };
}

async function main() {
  const data = await loadPagesJson();
  const pages = data.pages ?? [];
  const count = countKnowledge(pages);

  console.log(`磐田の集合知（公開記事数）: ${count} 本`);
  console.log(`data/pages.json 総ページ数: ${pages.length} 件`);

  const audit = await auditAgainstArticleIndex(pages);
  if (audit) {
    console.log("\n--- 監査レポート（c034.html 全記事一覧との突き合わせ） ---");
    console.log(`全記事一覧のユニークリンク数: ${audit.totalIndexed} 件`);

    if (audit.brokenLinks.length > 0) {
      fail(`リンク切れ（実体ファイルが見つからない）: ${audit.brokenLinks.length} 件`);
      for (const u of audit.brokenLinks) console.error(`   - ${u}`);
    }

    const missingButReal = audit.missing.filter((u) => !audit.brokenLinks.includes(u));
    if (missingButReal.length > 0) {
      fail(`data/pages.json に未登録: ${missingButReal.length} 件`);
      for (const u of missingButReal) console.error(`   - ${u}`);
    }

    if (audit.notCounted.length > 0) {
      const unexpected = audit.notCounted.filter((e) => e.status !== "archived");
      if (unexpected.length > 0) {
        fail(`登録済みだが count_as_knowledge が true でない: ${unexpected.length} 件`);
        for (const e of unexpected) console.error(`   - ${e.url} (status: ${e.status})`);
      }
      const archived = audit.notCounted.filter((e) => e.status === "archived");
      if (archived.length > 0) {
        console.log(`  (archived のため意図的に除外中: ${archived.length} 件)`);
      }
    }

    if (audit.orphaned.length > 0) {
      fail(`count_as_knowledge:true だが全記事一覧に未掲載: ${audit.orphaned.length} 件`);
      for (const u of audit.orphaned) console.error(`   - ${u}`);
    }

    if (
      audit.brokenLinks.length === 0 &&
      missingButReal.length === 0 &&
      audit.notCounted.every((e) => e.status === "archived") &&
      audit.orphaned.length === 0
    ) {
      console.log("✓ 全記事一覧と data/pages.json は一致しています。");
    }
  }

  if (AUDIT_ONLY) return;

  console.log("\n--- 表示先の同期 ---");
  for (const target of DISPLAY_TARGETS) {
    const result = await updateDisplayFile(target, count);
    const rel = path.relative(ROOT, result.path);
    if (!result.found) {
      console.log(`  (skip) ${rel} … data-knowledge-count 属性が見つかりません`);
    } else if (result.changed) {
      console.log(
        `  ${CHECK_MODE ? "(要更新)" : "✓ 更新"} ${rel} … ${count} 本に${CHECK_MODE ? "更新が必要です" : "更新しました"}`
      );
      if (CHECK_MODE) process.exitCode = 1;
    } else {
      console.log(`  = 変更なし ${rel} … すでに ${count} 本`);
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
