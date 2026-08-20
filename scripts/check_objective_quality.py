from __future__ import annotations

import csv
from html import unescape
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
OUTPUT = Path(tempfile.gettempdir()) / "iwata-objective-quality-audit"
OUTPUT.mkdir(parents=True, exist_ok=True)

for checker in ("check_heading_density.py", "check_content_quality.py", "check_objective_quality_detail.py"):
    result = subprocess.run(
        [sys.executable, str(BASE / checker)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(result.returncode)

report = json.loads((Path(tempfile.gettempdir()) / "iwata-deep-quality-audit.json").read_text(encoding="utf-8"))
pages = json.loads((ROOT / "data/pages.json").read_text(encoding="utf-8"))["pages"]
exempt = set(json.loads((ROOT / "data/content-quality-exemptions.json").read_text(encoding="utf-8"))["pages"])


def resolve(url):
    rel = str(url or "").split("?", 1)[0].split("#", 1)[0].lstrip("/").rstrip("/")
    for path in (ROOT / rel, ROOT / f"{rel}.html", ROOT / rel / "index.html"):
        if path.is_file():
            return path
    return None


def key_for(page):
    path = resolve(page.get("url"))
    return path.relative_to(ROOT).as_posix() if path else str(page.get("url"))


knowledge = {}
for page in pages:
    if page.get("count_as_knowledge"):
        knowledge[key_for(page)] = page

failures = {key: set() for key in knowledge}


def add(rule, keys):
    for key in keys:
        if key in failures and key not in exempt:
            failures[key].add(rule)


add("R06_METADATA", [x.split(":", 1)[0] for x in report["metadata_issues"]])
add("R07_INTERNAL_LINK", [x[0] for x in report["broken_internal_links"]])
add("R08_IMAGE_FILE", [x[0] for x in report["broken_images"]])
add("R09_IMAGE_ALT", [x[0] for x in report["missing_alt"]])
add("R10_FIGCAPTION", [x[0] for x in report["missing_figure_captions"]])
add("R11_SOURCE_MISSING", report["missing_sources"])
add("R12_SOURCE_WEAK", [x[0] for x in report["weak_source_pages"]])
add("R13_MEMO_RATIO", [x[0] for x in report["memo_like_pages"]])
add("R14_PROCESS_PROSE", [x[0] for x in report["pipeline_prose_pages"]])
add("R15_REPEAT_RATIO", [x[0] for x in report["pages_with_20pct_repeated_paragraphs"]])
add("R16_DUPLICATE_ARTICLE", [x[0] for x in report["high_similarity_same_h1_pairs"]] + [x[1] for x in report["high_similarity_same_h1_pairs"]])

# Rule R17: no single SVG topology may be reused on 10 or more assets.
bad_svg_assets = {
    src
    for count, assets in report["svg_topology_clusters"]
    if count >= 10
    for src in assets
}
for key in failures:
    path = ROOT / key
    if not path.is_file():
        continue
    raw = path.read_text(encoding="utf-8", errors="replace")
    sources = set(re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', raw, re.I))
    if sources & bad_svg_assets and key not in exempt:
        failures[key].add("R17_SVG_TEMPLATE")

# R01-R05 are already enforced by the production quality gate and passed for
# every non-exempt knowledge page. Keep them explicit in the rule ledger.
rules = {
    "R01_MIN_CHARS": "読み物本文1,800字以上",
    "R02_VISUAL_2500": "2,500字以上は図版1点以上",
    "R03_VISUAL_4000": "4,000字以上は図版2点以上",
    "R04_HEADING_DENSITY": "見出し間隔1,000字以上",
    "R05_BASE_DUPLICATION": "完全一致定型文比率35%未満",
    "R06_METADATA": "title・h1・description・canonicalが完全",
    "R07_INTERNAL_LINK": "内部リンクの到達不能0件",
    "R08_IMAGE_FILE": "画像ファイル破損0件",
    "R09_IMAGE_ALT": "画像alt欠落0件",
    "R10_FIGCAPTION": "figure内画像のfigcaption欠落0件",
    "R11_SOURCE_MISSING": "2,500字以上の記事に出典区画がある",
    "R12_SOURCE_WEAK": "具体的に追跡可能な出典項目が2件以上",
    "R13_MEMO_RATIO": "今後・追加調査など作業予定を含む段落が28%未満",
    "R14_PROCESS_PROSE": "編集・生成作業の内部表現0件",
    "R15_REPEAT_RATIO": "他記事と共通する80字以上の段落が本文の20%未満",
    "R16_DUPLICATE_ARTICLE": "同一h1かつ本文類似度70%以上の記事対0件",
    "R17_SVG_TEMPLATE": "同一構図SVGの使用は9点以下",
}

rule_counts = {rule: sum(rule in values for values in failures.values()) for rule in rules}
failed = {key: sorted(values) for key, values in failures.items() if values}
passed = sorted(key for key, values in failures.items() if not values)

summary = {
    "audit_date": "2026-08-20",
    "knowledge_pages": len(knowledge),
    "explicit_functional_exemptions": len(exempt),
    "passed_pages": len(passed),
    "failed_pages": len(failed),
    "pass_rate": round(len(passed) / len(knowledge), 4),
    "rules": rules,
    "rule_failure_counts": rule_counts,
    "failed": failed,
    "passed": passed,
}

json_path = OUTPUT / "objective-quality-audit-2026-08-20.json"
json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

csv_path = OUTPUT / "objective-quality-audit-2026-08-20.csv"
with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["page", "result", "failed_rules", "title", "url"])
    for key in sorted(knowledge):
        page = knowledge[key]
        values = sorted(failures[key])
        writer.writerow([key, "FAIL" if values else "PASS", "|".join(values), page.get("title", ""), page.get("url", "")])

md_path = OUTPUT / "objective-quality-audit-2026-08-20.md"
lines = [
    "# 磐田物語 客観的品質監査",
    "",
    "監査日: 2026-08-20",
    "",
    f"- 対象: {len(knowledge)}知識ページ",
    f"- 合格: {len(passed)}ページ",
    f"- 不合格: {len(failed)}ページ",
    f"- 合格率: {len(passed) / len(knowledge):.1%}",
    f"- 読み物ではない明示的除外: {len(exempt)}ページ",
    "",
    "## 判定ルールと不合格数",
    "",
]
for rule, label in rules.items():
    lines.append(f"- {rule}: {label} — {rule_counts[rule]}ページ不合格")
lines += ["", "## 不合格ページ", ""]
for key, values in sorted(failed.items()):
    lines.append(f"- `{key}`: {', '.join(values)}")
md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({
    "knowledge_pages": len(knowledge),
    "passed_pages": len(passed),
    "failed_pages": len(failed),
    "pass_rate": round(len(passed) / len(knowledge), 4),
    "rule_failure_counts": rule_counts,
    "files": [str(md_path), str(csv_path), str(json_path)],
}, ensure_ascii=False, indent=2))

if failed:
    print(f"objective quality FAILED: {len(failed)} knowledge pages", file=sys.stderr)
    raise SystemExit(1)
print(f"objective quality OK: {len(passed)} knowledge pages passed all 17 rules")
