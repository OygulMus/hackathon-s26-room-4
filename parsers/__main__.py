"""CLI: снять снимок по всем источникам и положить в data/snapshots/.

Печатает честную сводку: сколько источников ответили из скольких. Отчёт по
двум магазинам из пяти, поданный как полная картина, — та же ошибка, что
цифра времени без порога склейки.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from parsers.snapshot import build_snapshot
from parsers.shops import scrape
from parsers.sources import ALL_SOURCES

OUT = Path("data/snapshots")


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    OUT.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    ok = 0

    for src in ALL_SOURCES:
        item, status = scrape(src["url"], src["sku"], src["shop"])
        reachable = status == "ok"
        ok += reachable
        snap = build_snapshot(
            src["shop"], [item] if reachable else [],
            status="ok" if reachable else "unreachable")
        path = OUT / f"{today}-{src['shop']}.json"
        path.write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                        encoding="utf-8")

        if reachable:
            print(f"  {src['shop']:<18} {item['price']:>12,.0f} "
                  f"{item['currency']}  в наличии: "
                  f"{'да' if item['in_stock'] else 'нет'}")
        else:
            print(f"  {src['shop']:<18} {'—':>12}  недоступен: "
                  f"{status.split(':', 1)[-1]}")

    total = len(ALL_SOURCES)
    print(f"\nдоступно {ok} из {total} источников. "
          f"Позиции недоступных НЕ считаются пропавшими.")
    if ok < total:
        print("Картина неполная — это сказано вслух, а не спрятано в итоге.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
