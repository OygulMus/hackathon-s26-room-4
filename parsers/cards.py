"""Разбор карточки товара из HTML в позицию снимка.

Три ловушки из examples/02-парсинг-вёрстки/expected.md, из-за которых нельзя
просто «взять первое число на странице»:

1. **NBSP.** Цена приходит как `32&nbsp;100&nbsp;₽`. Обычный split по пробелу
   её не соберёт, а `int()` на такой строке падает.
2. **Зачёркнутая цена.** Рядом лежат `price-new` и `price-old`. Взять старую —
   значит завтра показать в дайджесте несуществующий рост.
3. **«Ожидается поставка».** Формально текст о наличии есть, фактически
   товара нет. Читать как отсутствие.

Плюс четвёртая, найденная на живых сайтах (docs/sources-proposal-4NNT.md):
цена-заглушка «по запросу» — не число, и в сравнение идти не должна.
"""

from __future__ import annotations

import re
import unicodedata
from html.parser import HTMLParser

# Приоритет важен: текущая цена ищется раньше старой.
PRICE_HINTS_CURRENT = ("price-new", "price_new", "js-price", "price-current",
                       "product-price", "price")
PRICE_HINTS_OLD = ("price-old", "price_old", "old-price", "was-price")

OUT_OF_STOCK_WORDS = ("ожидается", "под заказ", "нет в наличии", "распродан",
                      "недоступен", "out of stock", "backorder")
IN_STOCK_WORDS = ("в наличии", "есть в наличии", "in stock", "available")
ON_REQUEST_WORDS = ("по запросу", "уточняйте", "contact us", "request a quote")


def _clean(text: str) -> str:
    """NBSP, узкий пробел и прочая типографика — в обычный пробел."""
    text = unicodedata.normalize("NFKC", text.replace("\xa0", " "))
    return re.sub(r"\s+", " ", text).strip()


def to_number(text: str) -> float | None:
    """Число из ценовой строки. Возвращает None, если числа нет."""
    digits = re.sub(r"[^\d,.]", "", _clean(text).replace(" ", ""))
    digits = digits.replace(",", ".")
    if digits.count(".") > 1:  # 1.234.567 — разделители разрядов
        digits = digits.replace(".", "")
    if not re.search(r"\d", digits):
        return None
    try:
        return float(digits)
    except ValueError:
        return None


class _Card(HTMLParser):
    """Собирает из карточки: атрибуты, текст по классам, весь текст."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.attrs: dict[str, str] = {}
        self.by_class: list[tuple[str, str]] = []
        self.text_parts: list[str] = []
        self._stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        for key, value in d.items():
            if key.startswith("data-") or key == "content":
                self.attrs.setdefault(key, value or "")
            if key == "itemprop":
                self.attrs.setdefault(f"itemprop:{value}", d.get("content", ""))
        self._stack.append(" ".join(filter(None, [d.get("class", ""), tag])))

    def handle_endtag(self, tag):
        if self._stack:
            self._stack.pop()

    def handle_data(self, data):
        text = _clean(data)
        if not text:
            return
        self.text_parts.append(text)
        marker = self._stack[-1] if self._stack else ""
        self.by_class.append((marker.lower(), text))


def _pick(by_class, hints, exclude=()):
    for marker, text in by_class:
        if any(h in marker for h in exclude):
            continue
        if any(h in marker for h in hints):
            return text
    return None


def parse_card(html: str, *, shop: str = "", currency: str = "RUB") -> dict:
    """HTML одной карточки → позиция контракта v2."""
    p = _Card()
    p.feed(html)
    whole = _clean(" ".join(p.text_parts))

    sku = (p.attrs.get("data-sku") or p.attrs.get("data-article")
           or p.attrs.get("data-id") or "")
    title = _pick(p.by_class, ("title", "h3", "h2", "name")) or whole[:80]
    if not sku:
        m = re.search(r"\(([A-Z0-9][A-Z0-9\-]{5,})\)", title) or \
            re.search(r"\b([A-Z]{2,}[A-Z0-9\-]{5,})\b", title)
        sku = m.group(1) if m else ""

    raw_price = (p.attrs.get("data-price")
                 or p.attrs.get("itemprop:price")
                 or _pick(p.by_class, PRICE_HINTS_CURRENT, exclude=PRICE_HINTS_OLD))
    price = to_number(raw_price) if raw_price else None

    low = whole.lower()
    if price is None and any(w in low for w in ON_REQUEST_WORDS):
        price_status = "on_request"
    elif price is None:
        price_status = "unknown"
    else:
        price_status = "listed"

    if any(w in low for w in OUT_OF_STOCK_WORDS):
        in_stock = False
    elif any(w in low for w in IN_STOCK_WORDS):
        in_stock = True
    else:
        in_stock = False

    return {
        "sku": sku,
        "shop": shop,
        "title": title,
        "price": price,
        "currency": currency,
        "price_status": price_status,
        "in_stock": in_stock,
    }
