# -*- coding: utf-8 -*-
"""Фолбэк-дифф двух снимков — ВРЕМЕННЫЙ, до мержа модуля diff/ (issue #5).

Интерфейс, который core ждёт от diff/: diff_snapshots(a, b) -> list[event].
Event: {"type", "sku", "title", "from", "to", "pct", "currency", "note"}
types: price_change | back_in_stock | out_of_stock | new_item | gone
     | not_comparable | source_unreachable
Правила из issue #4:
- b.source_status == "unreachable" -> одно событие source_unreachable,
  позиции источника пропавшими НЕ считаются;
- price_status != "listed" -> цена в сравнение не идёт (not_comparable
  при смене статуса, иначе просто пропуск);
- сравнение цен только внутри одной валюты.
"""


def diff_snapshots(a, b):
    events = []
    if b.get("source_status") == "unreachable":
        events.append({"type": "source_unreachable", "sku": "",
                       "title": b.get("source", ""), "note": "источник недоступен"})
        return events

    a_items, b_items = a["items"], b["items"]

    for sku, bi in b_items.items():
        ai = a_items.get(sku)
        if ai is None:
            events.append({"type": "new_item", "sku": sku, "title": bi["title"],
                           "to": bi["price"], "currency": bi["currency"]})
            continue

        price_event = None
        comparable = (ai["price_status"] == "listed" == bi["price_status"]
                      and ai["currency"] == bi["currency"]
                      and ai["price"] is not None and bi["price"] is not None)
        if comparable and ai["price"] != bi["price"]:
            pct = round((bi["price"] - ai["price"]) / ai["price"] * 100, 1)
            price_event = {"type": "price_change", "sku": sku, "title": bi["title"],
                           "from": ai["price"], "to": bi["price"], "pct": pct,
                           "currency": bi["currency"]}
        elif not comparable and (ai["price_status"] != bi["price_status"]
                                 or ai["currency"] != bi["currency"]):
            price_event = {"type": "not_comparable", "sku": sku, "title": bi["title"],
                           "note": f'{ai["price_status"]}/{ai["currency"] or "?"} → '
                                   f'{bi["price_status"]}/{bi["currency"] or "?"}'}

        if not ai["in_stock"] and bi["in_stock"]:
            note = "цена без изменений" if price_event is None else None
            events.append({"type": "back_in_stock", "sku": sku,
                           "title": bi["title"], "note": note})
        elif ai["in_stock"] and not bi["in_stock"]:
            events.append({"type": "out_of_stock", "sku": sku, "title": bi["title"]})

        if price_event:
            events.append(price_event)

    for sku, ai in a_items.items():
        if sku not in b_items:
            events.append({"type": "gone", "sku": sku, "title": ai["title"],
                           "note": "не путать со снижением цены"})

    return events
