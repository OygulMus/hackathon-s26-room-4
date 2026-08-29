"""Прогон дифф-движка на examples/01-снимки-цен — приёмочная проверка модуля.

Запуск: python -m diff.run_example
Печатает получившийся дайджест и сверяет ключевые факты из expected.md
(проценты, появление/пропажа/новинка) программно, чтобы регресс был виден
сразу, а не только на глаз.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from diff import to_v2, compute_changes, render_digest

EXAMPLE_DIR = pathlib.Path(__file__).resolve().parent.parent / "examples" / "01-снимки-цен" / "input"


def load(name):
    with open(EXAMPLE_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    prev_raw = load("snapshot-2026-08-27.json")
    curr_raw = load("snapshot-2026-08-28.json")

    prev = to_v2(prev_raw)
    curr = to_v2(curr_raw)

    changes = compute_changes(prev, curr)
    digest = render_digest(prev["taken_at"], curr["taken_at"], changes)
    print(digest)

    by_sku = {c["sku"]: c for c in changes}

    checks = [
        ("MZ7L3960HCJR-00A07", "price_change", -5.3),
        ("ST16000NM004J", "price_change", 6.0),
        ("ST12000NM004J", "appeared", None),
        ("MZ7L33T8HBLT-00A07", "disappeared", None),
        ("ST24000NM002H", "new", None),
    ]

    ok = 0
    for sku, expected_kind, expected_pct in checks:
        change = by_sku.get(sku)
        if change is None:
            print(f"FAIL {sku}: изменение не найдено")
            continue
        if change["kind"] != expected_kind:
            print(f"FAIL {sku}: kind={change['kind']!r}, ожидали {expected_kind!r}")
            continue
        if expected_pct is not None:
            delta = change["delta_pct"]
            if abs(delta - expected_pct) > 0.1:
                print(f"FAIL {sku}: delta_pct={delta:.2f}, ожидали {expected_pct} ±0.1")
                continue
        ok += 1
        print(f"OK   {sku}: {expected_kind}")

    # expected.md говорит "остальные три" про заметные (недвусмысленные)
    # позиции без изменений; в примере всего 9 SKU, 5 из них меняются
    # (см. checks выше) — значит без изменений остаётся 4.
    unchanged_count = sum(1 for c in changes if c["kind"] == "unchanged")
    if unchanged_count == 4:
        ok += 1
        print(f"OK   без изменений: {unchanged_count} позиции")
    else:
        print(f"FAIL без изменений: {unchanged_count}, ожидали 4")

    total = len(checks) + 1
    print(f"\n{ok}/{total} проверок прошло")
    if ok != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
