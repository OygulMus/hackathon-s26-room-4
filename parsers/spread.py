"""Сравнение одной позиции между магазинами за один день.

`core/` отвечает на вопрос «что изменилось со вчера». Этот модуль отвечает на
второй вопрос из README комнаты — «в пяти онлайн-магазинах»: где сегодня
дешевле и насколько магазины расходятся между собой.

Разница принципиальная: динамика требует двух снимков во времени, разброс
виден по одному дню. На демо у нас есть только один день.

Честность та же, что везде: молчащие магазины называются поимённо. Разброс,
посчитанный по двум витринам из пяти и поданный без этой оговорки, — обман.
"""

from __future__ import annotations

import html as _html
import json
from pathlib import Path
from typing import Iterable


def load_snapshots(folder: str | Path) -> list[dict]:
    return [json.loads(Path(p).read_text(encoding="utf-8"))
            for p in sorted(Path(folder).glob("*.json"))]


def compare(snapshots: Iterable[dict]) -> dict:
    """Позиции, встреченные больше чем в одном магазине, + список молчащих."""
    snapshots = list(snapshots)
    silent = [s["source"] for s in snapshots if s.get("source_status") != "ok"]
    offers: dict[str, list[dict]] = {}

    for snap in snapshots:
        if snap.get("source_status") != "ok":
            continue
        for sku, item in snap.get("items", {}).items():
            if item.get("price_status") != "listed" or item.get("price") is None:
                continue
            offers.setdefault(sku, []).append(
                {"shop": item.get("shop") or snap["source"],
                 "price": float(item["price"]),
                 "currency": item.get("currency", ""),
                 "in_stock": bool(item.get("in_stock"))})

    rows = []
    for sku, found in sorted(offers.items()):
        by_currency: dict[str, list[dict]] = {}
        for offer in found:
            by_currency.setdefault(offer["currency"], []).append(offer)
        # Сравниваем только внутри одной валюты — правило контракта v2.
        for currency, same in by_currency.items():
            cheapest = min(same, key=lambda o: o["price"])
            dearest = max(same, key=lambda o: o["price"])
            rows.append({
                "sku": sku,
                "currency": currency,
                "offers": sorted(same, key=lambda o: o["price"]),
                "cheapest": cheapest,
                "dearest": dearest,
                "spread_percent": (
                    round((dearest["price"] / cheapest["price"] - 1) * 100, 1)
                    if cheapest["price"] else 0.0),
                "shops_compared": len(same),
            })

    return {"rows": rows, "silent_sources": silent,
            "sources_total": len(snapshots),
            "sources_ok": len(snapshots) - len(silent)}


def section_html(folder: str | Path) -> str:
    """Секция «где сегодня дешевле» для core/render.py — одна строка вызова."""
    data = compare(load_snapshots(folder))
    parts = ["<h2>Один товар в разных магазинах</h2>"]

    if not data["rows"]:
        parts.append('<div class="warnbox">Сравнивать не с чем: сегодня цену '
                     'отдал максимум один магазин.</div>')
        return "\n".join(parts)

    for row in data["rows"]:
        parts.append(
            f'<div class="unchanged">{_html.escape(row["sku"])} — разброс '
            f'<b>{row["spread_percent"]:.1f}%</b> по '
            f'{row["shops_compared"]} магазинам</div><ul>')
        for offer in row["offers"]:
            mark = "" if offer["in_stock"] else " · нет в наличии"
            price = f'{offer["price"]:,.0f}'.replace(",", " ")
            parts.append(
                f'<li>{_html.escape(offer["shop"])} — {price} '
                f'{_html.escape(offer["currency"])}{mark}</li>')
        parts.append("</ul>")

    if data["silent_sources"]:
        parts.append(
            f'<div class="warnbox">⚠️ Разброс посчитан по '
            f'{data["sources_ok"]} магазинам из {data["sources_total"]}. '
            f'Молчат: {_html.escape(", ".join(data["silent_sources"]))}. '
            f'Их позиции НЕ считаются пропавшими, и настоящий минимум может '
            f'быть ниже показанного.</div>')
    return "\n".join(parts)
