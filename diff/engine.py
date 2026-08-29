"""Дифф-движок: сравнение двух снимков (контракт v2) → список изменений.

Чистые функции: вход — два снимка в форме контракта v2 (см. adapters.py),
выход — список записей об изменениях. Ничего не печатает, ничего не читает
с диска — этим занимается core/ (issue #8) или CLI-обвязка в этом модуле
(run_example.py) для локальной проверки.

Правила (issue #4, решение лидера SQSU):
- `source_status: unreachable` у источника → позиции ЭТОГО источника не
  считаются пропавшими; в дайджест уходит отдельная строка «источник
  недоступен».
- `price_status != listed` → цена в сравнение не идёт (нет опоры для %).
- Сравнение цен только внутри одной валюты — конвертации нет; если валюта
  снимков разошлась для одного SKU, дельта не считается, это отдельный
  повод для строки в дайджесте, а не тихое обнуление.
- Пропажа из выдачи (SKU был — SKU нет) и уход "нет в наличии" (SKU есть,
  in_stock: false) — разные события, путать их с изменением цены нельзя.
"""


def _items(snapshot):
    """items может быть словарём {sku: item} (контракт v2) или списком
    объектов с полем sku (сырые данные поставщика до нормализации) —
    приводим к единому словарю."""
    raw = snapshot.get("items", {})
    if isinstance(raw, dict):
        return raw
    normalized = {}
    for entry in raw:
        sku = entry.get("sku")
        if sku is not None:
            normalized[sku] = entry
    return normalized


def _price_comparable(prev_item, curr_item):
    if prev_item.get("price_status", "listed") != "listed":
        return False
    if curr_item.get("price_status", "listed") != "listed":
        return False
    if prev_item.get("price") is None or curr_item.get("price") is None:
        return False
    prev_currency = prev_item.get("currency")
    curr_currency = curr_item.get("currency")
    if prev_currency and curr_currency and prev_currency != curr_currency:
        return False
    return True


def compute_changes(prev_snapshot, curr_snapshot):
    """Возвращает список dict-записей об изменениях между двумя снимками.

    Каждая запись содержит как минимум {"sku", "kind"}; остальные поля
    зависят от kind. kind ∈ {price_change, appeared, disappeared,
    went_out_of_stock, new, source_unreachable, currency_mismatch,
    price_unavailable, unchanged}.
    """
    prev_items = _items(prev_snapshot)
    curr_items = _items(curr_snapshot)
    curr_source_status = curr_snapshot.get("source_status", "ok")

    changes = []
    for sku in sorted(set(prev_items) | set(curr_items)):
        prev_item = prev_items.get(sku)
        curr_item = curr_items.get(sku)

        if curr_item is None:
            if curr_source_status == "unreachable":
                changes.append({
                    "sku": sku,
                    "kind": "source_unreachable",
                    "title": prev_item.get("title", sku),
                    "shop": prev_item.get("shop"),
                })
            else:
                changes.append({
                    "sku": sku,
                    "kind": "disappeared",
                    "title": prev_item.get("title", sku),
                    "shop": prev_item.get("shop"),
                    "last_price": prev_item.get("price"),
                    "currency": prev_item.get("currency"),
                })
            continue

        if prev_item is None:
            changes.append({
                "sku": sku,
                "kind": "new",
                "title": curr_item.get("title", sku),
                "shop": curr_item.get("shop"),
                "price": curr_item.get("price"),
                "currency": curr_item.get("currency"),
                "price_status": curr_item.get("price_status", "listed"),
            })
            continue

        prev_in_stock = prev_item.get("in_stock", True)
        curr_in_stock = curr_item.get("in_stock", True)

        if not prev_in_stock and curr_in_stock:
            changes.append({
                "sku": sku,
                "kind": "appeared",
                "title": curr_item.get("title", sku),
                "shop": curr_item.get("shop"),
            })
            continue

        if prev_in_stock and not curr_in_stock:
            changes.append({
                "sku": sku,
                "kind": "went_out_of_stock",
                "title": curr_item.get("title", sku),
                "shop": curr_item.get("shop"),
                "last_price": prev_item.get("price"),
                "currency": prev_item.get("currency"),
            })
            continue

        if _price_comparable(prev_item, curr_item):
            prev_price = prev_item["price"]
            curr_price = curr_item["price"]
            if prev_price != curr_price:
                delta_pct = (curr_price - prev_price) / prev_price * 100
                changes.append({
                    "sku": sku,
                    "kind": "price_change",
                    "title": curr_item.get("title", sku),
                    "shop": curr_item.get("shop"),
                    "prev_price": prev_price,
                    "curr_price": curr_price,
                    "delta_pct": delta_pct,
                    "currency": curr_item.get("currency"),
                })
                continue
        else:
            prev_currency = prev_item.get("currency")
            curr_currency = curr_item.get("currency")
            if prev_currency and curr_currency and prev_currency != curr_currency:
                changes.append({
                    "sku": sku,
                    "kind": "currency_mismatch",
                    "title": curr_item.get("title", sku),
                    "shop": curr_item.get("shop"),
                    "prev_currency": prev_currency,
                    "curr_currency": curr_currency,
                })
                continue
            if curr_item.get("price_status", "listed") != "listed":
                changes.append({
                    "sku": sku,
                    "kind": "price_unavailable",
                    "title": curr_item.get("title", sku),
                    "shop": curr_item.get("shop"),
                    "price_status": curr_item.get("price_status"),
                })
                continue

        changes.append({
            "sku": sku,
            "kind": "unchanged",
            "title": curr_item.get("title", sku),
            "shop": curr_item.get("shop"),
        })

    return changes
