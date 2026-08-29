"""Адаптеры входных форматов снимков к контракту v2.

Контракт v2 (issue #4, решение лидера комнаты SQSU):

    {
      "taken_at": "ISO-8601",
      "source": "домен",
      "source_status": "ok" | "unreachable",
      "items": {
        "sku": {
          "shop": "...",
          "title": "...",
          "price": 13500.0,
          "currency": "USD",
          "price_status": "listed" | "on_request" | "unknown",
          "in_stock": true
        }
      }
    }

Старый плоский формат (examples/01-снимки-цен, `{date, items: {ID: {shop,
price, in_stock}}}`) не знает про currency/price_status/source_status —
считаем такой снимок одним всегда доступным источником, где все цены
подтверждены продавцом.
"""

LEGACY_DEFAULT_CURRENCY = None  # валюта не указана — сравнивается только сама с собой
LEGACY_PRICE_STATUS = "listed"
LEGACY_SOURCE_STATUS = "ok"


def is_legacy_snapshot(raw):
    """Плоский формат отличается ключом `date` и отсутствием `taken_at`."""
    return "date" in raw and "taken_at" not in raw


def adapt_legacy(raw):
    """Приводит плоский снимок examples/01 к форме контракта v2."""
    items = {}
    for sku, item in raw.get("items", {}).items():
        items[sku] = {
            "shop": item.get("shop"),
            "title": item.get("title", sku),
            "price": item.get("price"),
            "currency": item.get("currency", LEGACY_DEFAULT_CURRENCY),
            "price_status": item.get("price_status", LEGACY_PRICE_STATUS),
            "in_stock": item.get("in_stock", True),
        }
    return {
        "taken_at": raw.get("date"),
        "source": raw.get("source", "legacy"),
        "source_status": raw.get("source_status", LEGACY_SOURCE_STATUS),
        "items": items,
    }


def to_v2(raw):
    """Универсальный вход: v2-снимок пропускается как есть, легаси — адаптируется."""
    if is_legacy_snapshot(raw):
        return adapt_legacy(raw)
    return raw
