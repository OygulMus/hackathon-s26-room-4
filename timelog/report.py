"""Готовая секция для веб-дайджеста `core/render.py`.

Модуль отдаёт кусок HTML, а не правит чужой рендер: `core/` вызывает одну
функцию и вставляет результат. Разметка использует те же классы, что и
остальной дайджест, поэтому стилей добавлять не нужно.
"""

from __future__ import annotations

import html as _html
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from timelog.blocks import build_blocks, total_minutes

DEFAULT_THRESHOLDS = (10, 40)


def load_events(source: Any) -> list[dict]:
    """Принимает путь к jsonl либо готовый список событий."""
    if isinstance(source, (str, Path)):
        with Path(source).open(encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
    return list(source)


def summarize(
    source: Any, thresholds: Sequence[int] = DEFAULT_THRESHOLDS
) -> dict[str, Any]:
    """Машиночитаемая сводка: по расчёту на каждый порог + разброс."""
    events = load_events(source)
    runs = []
    for n in thresholds:
        blocks = build_blocks(events, n)
        runs.append(
            {
                "threshold_minutes": n,
                "blocks": [
                    {"label": b.label, "minutes": round(b.minutes, 1),
                     "single_event": b.single_event}
                    for b in blocks
                ],
                "total_minutes": round(total_minutes(blocks), 1),
            }
        )
    totals = [r["total_minutes"] for r in runs] or [0.0]
    lo, hi = min(totals), max(totals)
    return {
        "runs": runs,
        "min_total": lo,
        "max_total": hi,
        "spread_percent": round((hi / lo - 1) * 100, 1) if lo else 0.0,
    }


def section_html(
    source: Any, thresholds: Sequence[int] = DEFAULT_THRESHOLDS
) -> str:
    """Секция «время из логов» для веб-дайджеста.

    Ни одна цифра не выводится без порога, при котором она получена, —
    критерий заказчика 4NNT (docs/interview-4NNT.md).
    """
    s = summarize(source, thresholds)
    parts = ["<h2>Время из логов сессий</h2>"]
    for run in s["runs"]:
        parts.append(
            f'<div class="unchanged">порог склейки N = '
            f'{run["threshold_minutes"]} мин — итого '
            f'<b>{round(run["total_minutes"])} мин</b></div><ul>'
        )
        for b in run["blocks"]:
            flag = " · одно событие" if b["single_event"] else ""
            parts.append(
                f'<li>{_html.escape(b["label"])} — {b["minutes"]:.1f} мин{flag}</li>'
            )
        parts.append("</ul>")
    parts.append(
        f'<div class="warnbox">⚠️ Цифра зависит от порога склейки: от '
        f'{round(s["min_total"])} до {round(s["max_total"])} мин, разброс '
        f'{s["spread_percent"]:.0f}%. Одно число без названного порога — '
        f'не факт, а иллюзия факта.</div>'
    )
    return "\n".join(parts)
