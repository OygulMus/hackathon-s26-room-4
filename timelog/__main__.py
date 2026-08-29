"""CLI модуля timelog.

Единственное жёсткое требование заказчика 4NNT: цифра времени не выдаётся
без указанного порога склейки N. Поэтому вывод всегда парный — два порога
рядом, с границами блоков и с арифметикой, по которой сумма собрана.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from timelog.blocks import build_blocks, total_minutes

DEFAULT_THRESHOLDS = (10, 40)


def read_events(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def report(events: list[dict], thresholds=DEFAULT_THRESHOLDS) -> str:
    out: list[str] = ["СВОДКА ВРЕМЕНИ ПО ЛОГАМ СЕССИЙ", ""]
    totals = {}
    for n in thresholds:
        blocks = build_blocks(events, n)
        total = total_minutes(blocks)
        totals[n] = total
        out.append(f"порог склейки N = {n} мин")
        for b in blocks:
            flag = "  (одно событие)" if b.single_event else ""
            out.append(f"    {b.label}   {b.minutes:5.1f} мин{flag}")
        parts = " + ".join(f"{b.minutes:.1f}" for b in blocks)
        out.append(f"    итого: {parts} = {total:.1f} мин ≈ {round(total)} мин")
        out.append("")

    lo, hi = min(totals.values()), max(totals.values())
    spread = (hi / lo - 1) * 100 if lo else 0.0
    out.append(
        f"чувствительность к порогу: от {round(lo)} до {round(hi)} мин "
        f"— разброс {spread:.0f}% от одного параметра."
    )
    out.append("Число без названного порога смысла не имеет и здесь не выдаётся.")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("-")]
    flags = {a for a in argv[1:] if a.startswith("-")}

    if "--total-only" in flags:
        print(
            "Отказано: --total-only выдал бы одно число без порога склейки. "
            "Порог меняет ответ почти вдвое, поэтому цифра без него — не факт, "
            "а иллюзия факта. Критерий заказчика 4NNT, docs/interview-4NNT.md.",
            file=sys.stderr,
        )
        return 2

    if not args:
        print("использование: python -m timelog <sessions.jsonl>", file=sys.stderr)
        return 2

    print(report(read_events(Path(args[0]))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
