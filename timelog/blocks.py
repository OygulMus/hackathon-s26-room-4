"""Склейка событий агентской сессии в рабочие блоки.

Правило (examples/03-время-из-логов/expected.md): события с паузой между
соседними ≤ N минут — один блок; пауза больше — блок закрылся на последнем
событии.

Одна поправка к буквальному чтению правила, без которой пример не сходится
сам с собой. В выборке есть пауза 46.3 мин между `tool_call` (11:12:40) и
`assistant_msg` (11:58:59), а expected.md держит их в ОДНОМ блоке 11:10–11:59
при обоих порогах, N=10 и N=40. Объяснение одно: пока агент ждёт инструмент,
он работает, а не простаивает. Поэтому пауза ПОСЛЕ `tool_call` не закрывает
блок. Поведение включается флагом `work_through_tool_calls` (по умолчанию да)
— чтобы допущение было видимым, а не зашитым молча.

Модуль ничего не печатает и не выбирает «правильный» порог: показ порога
рядом с числом — требование заказчика 4NNT (docs/interview-4NNT.md), и держит
его CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable, Sequence

WORK_EVENTS = frozenset({"tool_call"})


@dataclass(frozen=True)
class Block:
    """Один непрерывный кусок работы."""

    start: datetime
    end: datetime
    events: int

    @property
    def minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60.0

    @property
    def single_event(self) -> bool:
        """Блок из одного события: длительность 0, но факт работы был.
        Не выбрасываем молча — иначе короткие заходы исчезают, и сумма
        занижается необъяснимо."""
        return self.events == 1

    @property
    def label(self) -> str:
        """Начало — минута первого события. Конец округляется до ближайшей
        минуты: событие в 11:58:59 читается человеком как 11:59, а не 11:58."""
        end = self.end + timedelta(seconds=30)
        return f"{self.start:%H:%M}–{end:%H:%M}"

    def __str__(self) -> str:
        return self.label


def _parse(event: Any) -> tuple[datetime, str]:
    if isinstance(event, dict):
        return (
            datetime.fromisoformat(str(event["ts"]).replace("Z", "+00:00")),
            str(event.get("event", "")),
        )
    return datetime.fromisoformat(str(event).replace("Z", "+00:00")), ""


def build_blocks(
    events: Iterable[Any],
    gap_minutes: float,
    *,
    work_through_tool_calls: bool = True,
) -> list[Block]:
    """Склеить события в блоки при пороге `gap_minutes`.

    Порог включительный: пауза ровно N минут оставляет события в одном блоке.
    """
    if gap_minutes < 0:
        raise ValueError("порог склейки не может быть отрицательным")

    parsed = sorted((_parse(e) for e in events), key=lambda p: p[0])
    if not parsed:
        return []

    gap = timedelta(minutes=gap_minutes)
    blocks: list[Block] = []
    start = prev_ts = parsed[0][0]
    prev_kind = parsed[0][1]
    count = 1

    for ts, kind in parsed[1:]:
        waiting_on_tool = work_through_tool_calls and prev_kind in WORK_EVENTS
        if ts - prev_ts <= gap or waiting_on_tool:
            count += 1
        else:
            blocks.append(Block(start, prev_ts, count))
            start, count = ts, 1
        prev_ts, prev_kind = ts, kind

    blocks.append(Block(start, prev_ts, count))
    return blocks


def total_minutes(blocks: Sequence[Block]) -> float:
    """Сумма длительностей блоков. Само по себе это число НЕ отчёт: без
    названного порога оно бессмысленно — см. timelog/__main__.py."""
    return sum(b.minutes for b in blocks)
