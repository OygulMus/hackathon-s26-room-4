# -*- coding: utf-8 -*-
"""CLI оркестратора: снимки -> дайджест (markdown + html).

Примеры:
  python -m core.build --pair examples/01-снимки-цен/input/snapshot-2026-08-27.json \
                              examples/01-снимки-цен/input/snapshot-2026-08-28.json
  python -m core.build --data data/snapshots --out-dir site

--data: в папке лежат снимки *.json (любой поддерживаемый формат);
группируются по source, внутри источника сравниваются два последних по дате.
"""

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from core import digest as dg
from core import render, snapshot

# когда участник issue #5 вольёт модуль diff/ — переключимся на него
try:
    from diff.engine import diff_snapshots  # type: ignore
except ImportError:
    from core.fallback_diff import diff_snapshots


def pairs_from_dir(data_dir):
    by_source = {}
    for p in sorted(pathlib.Path(data_dir).rglob("*.json")):
        try:
            snap = snapshot.load(p)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"! пропущен {p}: {e}", file=sys.stderr)
            continue
        by_source.setdefault(snap["source"] or p.parent.name, []).append(snap)
    pairs = []
    for source, snaps in sorted(by_source.items()):
        snaps.sort(key=lambda s: s["taken_at"])
        if len(snaps) < 2:
            print(f"! {source}: один снимок, сравнивать не с чем", file=sys.stderr)
            continue
        a, b = snaps[-2], snaps[-1]
        # одна битая пара не должна валить дайджест всех источников (issue #15)
        try:
            events = diff_snapshots(a, b)
        except Exception as e:  # noqa: BLE001 — на демо важнее пережить, чем упасть
            events = [{"type": "diff_error", "sku": "", "title": source,
                       "note": f"{type(e).__name__}: {e}"}]
        pairs.append((a, b, events))
    return pairs


def main(argv=None):
    ap = argparse.ArgumentParser(description="снимки -> дайджест изменений")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pair", nargs=2, metavar=("A", "B"), help="два снимка одного источника")
    g.add_argument("--data", help="папка со снимками, группировка по source")
    ap.add_argument("--out-dir", default="out", help="куда класть digest.md и index.html")
    ap.add_argument("--red", type=float, default=dg.RED_PCT, help="порог красного, %%")
    ap.add_argument("--warn", type=float, default=dg.WARN_PCT, help="порог жёлтого, %%")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    if args.pair:
        try:
            a, b = snapshot.load(args.pair[0]), snapshot.load(args.pair[1])
        except (OSError, json.JSONDecodeError, KeyError) as e:
            print(f"! снимок не читается: {e}", file=sys.stderr)
            return 1
        pairs = [(a, b, diff_snapshots(a, b))]
    else:
        pairs = pairs_from_dir(args.data)
    if not pairs:
        print("нет пар снимков — дайджест не собран", file=sys.stderr)
        return 1

    d = dg.build_digest(pairs, red=args.red, warn=args.warn)
    md = dg.to_markdown(d)

    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "digest.md").write_text(md, encoding="utf-8")
    (out / "index.html").write_text(render.to_html(d), encoding="utf-8")

    print(md)
    print(f"→ {out / 'digest.md'}\n→ {out / 'index.html'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
