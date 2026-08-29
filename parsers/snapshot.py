"""Сборка снимка контракта v2 из разобранных позиций.

Главное правило (issue #4): недоступный источник даёт `source_status:
unreachable` и ПУСТОЙ список позиций. Пустой список при `ok` означал бы, что
все товары пропали из выдачи — это ложь, из-за которой дайджест покажет
несуществующую катастрофу.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable


def build_snapshot(source: str, items: Iterable[dict], *,
                   status: str = "ok", taken_at: str | None = None) -> dict:
    by_sku: dict[str, dict] = {}
    for item in items:
        sku = item.get("sku")
        if not sku:
            continue
        by_sku[sku] = {
            "shop": item.get("shop") or source,
            "title": item.get("title", sku),
            "price": item.get("price"),
            "currency": item.get("currency", "RUB"),
            "price_status": item.get("price_status", "unknown"),
            "in_stock": bool(item.get("in_stock", False)),
        }
    return {
        "taken_at": taken_at or datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "source_status": status,
        "items": {} if status != "ok" else by_sku,
    }
