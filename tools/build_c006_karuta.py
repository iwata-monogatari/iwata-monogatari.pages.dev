"""遠州弁かるた（/c006）の絵札を、元画から配信用 WebP に変換する。

元画はリポジトリの外の作業フォルダに置き、ファイル名を語ID（data/c006-dictionary.json の id）にする。
  例: <元画フォルダ>/aisa.png → assets/karuta/c006/aisa-300.webp と aisa-900.webp

使い方:
  python tools/build_c006_karuta.py --src <元画フォルダ>            # フォルダ内の全語を変換
  python tools/build_c006_karuta.py --src <元画フォルダ> --only aisa,dara
  python tools/build_c006_karuta.py --check                         # 配信ファイルの寸法と対応を検査
変換後に node tools/build_c006_dictionary.mjs（または npm run build）を実行すると、辞典に絵札が表示される。
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'assets/karuta/c006'
SIZES = {'300': (300, 400), '900': (900, 1200)}
QUALITY = {'300': 80, '900': 84}
MIN_SOURCE = (900, 1200)
RATIO = 3 / 4
RATIO_TOLERANCE = 0.02
THUMB_WARN_BYTES = 40_000
SOURCE_SUFFIXES = ('.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff')


def word_ids():
    data = json.loads((ROOT / 'data/c006-dictionary.json').read_text(encoding='utf8'))
    return {e['id'] for e in data['entries']}


def check_source(path: Path, image: Image.Image):
    w, h = image.size
    if w < MIN_SOURCE[0] or h < MIN_SOURCE[1]:
        raise ValueError(f'{path.name}: {w}x{h} は小さすぎます（{MIN_SOURCE[0]}x{MIN_SOURCE[1]} 以上、推奨 1200x1600）')
    if abs(w / h - RATIO) > RATIO_TOLERANCE:
        raise ValueError(f'{path.name}: 縦横比 {w}:{h} は 3:4 ではありません')


def convert(path: Path, out_dir: Path = OUT_DIR):
    with Image.open(path) as src:
        image = ImageOps.exif_transpose(src)
        check_source(path, image)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGBA')
            background = Image.new('RGB', image.size, (255, 253, 247))
            background.paste(image, mask=image.getchannel('A'))
            image = background
        else:
            image = image.convert('RGB')
        out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for key, size in SIZES.items():
            target = out_dir / f'{path.stem}-{key}.webp'
            ImageOps.fit(image, size, Image.Resampling.LANCZOS).save(target, 'WEBP', quality=QUALITY[key], method=6)
            written.append(target)
        return written


def check_outputs(out_dir: Path = OUT_DIR, ids=None):
    ids = ids if ids is not None else word_ids()
    problems = []
    if not out_dir.exists():
        return problems
    for f in sorted(out_dir.iterdir()):
        if f.name in ('README.md', '.gitkeep'):
            continue
        stem, _, key = f.stem.rpartition('-')
        if f.suffix != '.webp' or key not in SIZES:
            problems.append(f'想定外のファイル: {f.name}')
            continue
        if stem not in ids:
            problems.append(f'辞典にない語ID: {f.name}')
        with Image.open(f) as im:
            if im.size != SIZES[key]:
                problems.append(f'{f.name}: {im.size[0]}x{im.size[1]}（{SIZES[key][0]}x{SIZES[key][1]} のはず）')
        pair = out_dir / f'{stem}-{"900" if key == "300" else "300"}.webp'
        if not pair.exists():
            problems.append(f'{f.name} の対になるファイルがありません: {pair.name}')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--src', type=Path, help='元画フォルダ（リポジトリの外）')
    parser.add_argument('--only', help='変換する語IDをカンマ区切りで指定')
    parser.add_argument('--check', action='store_true', help='配信ファイルを検査するだけ')
    args = parser.parse_args(argv)
    ids = word_ids()
    if args.check:
        problems = check_outputs(ids=ids)
        for p in problems:
            print(p, file=sys.stderr)
        count = len(list(OUT_DIR.glob('*-300.webp'))) if OUT_DIR.exists() else 0
        print(f'c006 karuta: {count}/{len(ids)} 語の絵札, 問題 {len(problems)} 件')
        return 1 if problems else 0
    if not args.src:
        parser.error('--src か --check を指定してください')
    src = args.src.resolve()
    if src == ROOT or ROOT in src.parents:
        parser.error('元画フォルダはリポジトリの外に置いてください（配信用 WebP だけをリポジトリに入れます）')
    only = set(filter(None, (args.only or '').split(',')))
    unknown = only - ids
    if unknown:
        parser.error(f'辞典にない語ID: {", ".join(sorted(unknown))}')
    sources = sorted(p for p in src.iterdir() if p.suffix.lower() in SOURCE_SUFFIXES and (not only or p.stem in only))
    errors = 0
    for p in sources:
        if p.stem not in ids:
            print(f'skip: {p.name}（ファイル名が語IDではありません）', file=sys.stderr)
            continue
        try:
            written = convert(p)
        except ValueError as e:
            print(f'error: {e}', file=sys.stderr)
            errors += 1
            continue
        thumb = written[0].stat().st_size
        note = f'  ※サムネイル {thumb // 1000}KB（目安 40KB 以下）' if thumb > THUMB_WARN_BYTES else ''
        print(f'ok: {p.name} → {", ".join(w.name for w in written)}{note}')
    print('次に node tools/build_c006_dictionary.mjs を実行すると辞典に反映されます。')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
