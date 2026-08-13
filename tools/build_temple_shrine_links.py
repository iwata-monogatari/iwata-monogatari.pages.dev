# -*- coding: utf-8 -*-
"""ATAWI TEMPLE / ATAWI SHRINE のマスターデータから、磐田物語の本文自動リンク用の
対応表 data/temple-shrine-links.json を生成する。

  python tools/build_temple_shrine_links.py

マスターの所在は環境変数で上書きできる。
  ATAWI_TEMPLE_JSON  … atawi-temple/data/temples.json
  ATAWI_SHRINE_JSON  … atawi-shrine/workshop/data/shrines.json

生成物は「表層形（本文に現れる寺社名）→ リンク先」の辞書である。
手作業の調整（除外語・ブロック語・ページ別の同名解決）は data/temple-shrine-links.manual.json
に置き、このスクリプトが読み込んでマージする。マスターが更新されたら再実行すればよい。
"""
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

TEMPLE_JSON = os.environ.get(
    "ATAWI_TEMPLE_JSON",
    r"C:\Users\Owner\Desktop\work_claude\atawi-temple\data\temples.json",
)
SHRINE_JSON = os.environ.get(
    "ATAWI_SHRINE_JSON",
    r"C:\Users\Owner\Desktop\大石端末\99大石制作物\00ATAWI SHRINE\atawi-shrine\workshop\data\shrines.json",
)

OUT = os.path.join(REPO, "data", "temple-shrine-links.json")
MANUAL = os.path.join(REPO, "data", "temple-shrine-links.manual.json")

TEMPLE_BASE = "https://temple.atawi.link/temples/%s/"
SHRINE_BASE = "https://shrine.atawi.link/shrines/%s/"

AREAS = ["見付", "中泉", "御厨", "豊田", "南部", "向陽", "竜洋", "福田", "豊岡"]

KANA_ONLY = re.compile(r"^[ぁ-んァ-ヶー・]+$")
NOTE = re.compile(r"[（(][^（()）]*[）)]")


def load(path, label):
    if not os.path.exists(path):
        sys.exit("マスターが見つかりません（%s）: %s" % (label, path))
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def clean_alias(alias):
    """「万然寺（新字体表記）」→「万然寺」のように注記を落とす。"""
    return NOTE.sub("", alias).strip()


ADDR_OAZA = re.compile(r"磐田市([^0-9０-９]+)")


def raw_oaza(entry):
    """大字（字名）。神社は oaza、寺院は住所から取り出す。"""
    if entry.get("oaza"):
        return entry["oaza"].strip()
    m = ADDR_OAZA.search(entry.get("address") or "")
    if m:
        return re.sub(r"[０-９0-9丁目番地の\-]+$", "", m.group(1)).strip()
    return ""


def oaza_keys(entry, vocabulary):
    """大字レベルの地名キー。「豊浜中野」は「豊浜」「中野」にも展開する
    （本文では「中野白山神社」のように略して書かれるため）。"""
    oaza = raw_oaza(entry)
    if not oaza:
        return []
    keys = [oaza]
    for cut in range(2, len(oaza) - 1):
        head, tail = oaza[:cut], oaza[cut:]
        # 意味のある地名同士に割れるときだけ採用する（「惣兵|衛下新田」は捨てる）
        if head in vocabulary and len(tail) >= 2:
            keys += [head, tail]
    out = []
    for k in keys:
        if len(k) >= 2 and k not in out:
            out.append(k)
    return out


def _own(slug, key_map):
    """その候補だけが持つキー（他候補と重ならないもの）を返す。"""
    others = set()
    for s, keys in key_map.items():
        if s != slug:
            others.update(keys)
    return [k for k in key_map[slug] if k not in others]


def main():
    temples = load(TEMPLE_JSON, "temples.json")
    shrines = load(SHRINE_JSON, "shrines.json")["shrines"]

    entries = {}
    for t in temples:
        entries[t["slug"]] = {
            "kind": "temple",
            "slug": t["slug"],
            "name": t["name"],
            "area": t.get("area"),
            "oaza": None,
            "address": t.get("address"),
            "url": TEMPLE_BASE % t["slug"],
            "aliases": t.get("aliases") or [],
        }
    for s in shrines:
        entries[s["slug"]] = {
            "kind": "shrine",
            "slug": s["slug"],
            "name": s["name"],
            "area": s.get("area"),
            "oaza": s.get("oaza"),
            "address": s.get("address"),
            "url": SHRINE_BASE % s["slug"],
            "aliases": s.get("aliases") or [],
        }

    manual = {}
    if os.path.exists(MANUAL):
        with io.open(MANUAL, encoding="utf-8") as fh:
            manual = json.load(fh)
    exclude = set(manual.get("exclude_surfaces") or [])
    block_forms = manual.get("block_forms") or []
    external_markers = manual.get("external_markers") or []
    page_hints = manual.get("page_hints") or {}
    extra_surfaces = manual.get("extra_surfaces") or {}

    # ---- 表層形の収集 ----
    surfaces = collections.defaultdict(list)   # 表層形 -> [slug, ...]
    dropped = collections.defaultdict(list)
    for slug, e in entries.items():
        forms = [e["name"]] + [clean_alias(a) for a in e["aliases"]]
        for f in forms:
            f = f.strip()
            if not f:
                continue
            if len(f) < 3:
                dropped["短すぎる"].append((f, slug))
                continue
            if KANA_ONLY.match(f):
                dropped["読みがな"].append((f, slug))
                continue
            if f.endswith("山"):
                # 山号のみ（松林山＝松林山古墳、風祭山など地名と衝突する）
                dropped["山号のみ"].append((f, slug))
                continue
            if slug not in surfaces[f]:
                surfaces[f].append(slug)

    for f, slug in extra_surfaces.items():
        surfaces[f] = [slug]

    for f in list(surfaces):
        if f in exclude:
            dropped["手動除外"].append((f, ",".join(surfaces[f])))
            del surfaces[f]

    # ---- 一意／同名の振り分け ----
    # 地名として通用する語の辞書（大字の分割判定に使う）
    vocabulary = set(AREAS)
    for e in entries.values():
        o = raw_oaza(e)
        if o:
            vocabulary.add(o)

    unique = {}
    ambiguous = {}
    for f, slugs in surfaces.items():
        if len(slugs) == 1:
            unique[f] = slugs[0]
            continue
        # 大字レベル → 地区レベルの二段構えにする。
        # 「下太（大字）」と「南部（地区）」を同列に扱うと、南部地区の記事で
        # 下太の社と万正寺の社が両方ヒットして永久に決まらないため。
        oaza_map = {s: oaza_keys(entries[s], vocabulary) for s in slugs}
        area_map = {s: ([entries[s]["area"]] if entries[s].get("area") else []) for s in slugs}
        cands = []
        for slug in slugs:
            cands.append({
                "slug": slug,
                "oaza_keys": _own(slug, oaza_map),
                "area_keys": _own(slug, area_map),
            })
        ambiguous[f] = cands

    data = {
        "version": 2,
        "generated_by": "tools/build_temple_shrine_links.py",
        "source": {
            "temples": os.path.basename(TEMPLE_JSON),
            "shrines": os.path.basename(SHRINE_JSON),
            "temple_count": len(temples),
            "shrine_count": len(shrines),
        },
        "targets": {
            slug: {"kind": e["kind"], "name": e["name"], "url": e["url"]}
            for slug, e in sorted(entries.items())
        },
        "unique_surfaces": dict(sorted(unique.items())),
        "ambiguous_surfaces": dict(sorted(ambiguous.items())),
        "block_forms": block_forms,
        "external_markers": external_markers,
        "page_hints": page_hints,
    }

    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("寺院 %d件 / 神社 %d件" % (len(temples), len(shrines)))
    print("表層形: 一意 %d / 同名 %d" % (len(unique), len(ambiguous)))
    for reason, items in sorted(dropped.items()):
        print("  除外(%s): %d件" % (reason, len(items)))
    print("→ %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
