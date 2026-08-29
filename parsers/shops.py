"""Живые магазины из PR #9 (кейс заказчика Алексея) и PR #3.

Проверено 29.08.2026: из пяти магазинов по парт-номеру MZILG7T6HBLA-00A07
отдаются двое. Остальные три закрываются по-разному, и это не одно и то же:

  xcom-shop.ru ... 200, цена в schema.org ........... берётся
  regard.ru ...... 200, цена в schema.org ........... берётся
  onlinetrade.ru . 200, но тело 1.8 КБ — заглушка ... САМЫЙ ОПАСНЫЙ СЛУЧАЙ
  kns.ru ......... 200, капча по IP ................. unreachable
  citilink.ru .... 429 ............................... unreachable

Опасен именно третий: код успешный, а данных нет. Поэтому «успех» определяется
не кодом ответа, а наличием цены в теле, плюс порог на размер страницы.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from typing import NamedTuple

from parsers.cards import _clean, to_number

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

# Страница короче этого — почти наверняка заглушка антибота, а не товар.
MIN_REAL_PAGE_BYTES = 50_000

CAPTCHA_MARKERS = ("капч", "captcha", "похожи на автоматические",
                   "проверка браузера", "cloudflare")


class Fetched(NamedTuple):
    ok: bool
    body: str
    reason: str


def fetch(url: str, timeout: int = 20) -> Fetched:
    """Скачать страницу. `ok=False` — источник недоступен, с причиной."""
    request = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as exc:
        return Fetched(False, "", f"HTTP {exc.code}")
    except Exception as exc:                      # сеть, TLS, таймаут
        return Fetched(False, "", type(exc).__name__)

    return Fetched(True, body, "")


def classify_failure(body: str) -> str:
    """Почему на странице нет цены. Порядок проверок важен: слово «captcha»
    встречается и в скриптах нормальных витрин, поэтому маркер засчитывается
    только на короткой странице, где кроме заглушки ничего нет."""
    size = len(body.encode())
    low = body.lower()
    if size < MIN_REAL_PAGE_BYTES:
        if any(marker in low for marker in CAPTCHA_MARKERS):
            return f"капча, тело {size} байт"
        return f"заглушка, тело {size} байт"
    return "цены нет в теле страницы"


def extract_schema_price(html: str) -> dict:
    """Цена и наличие из микроразметки schema.org — так отдают оба рабочих
    магазина, и это устойчивее, чем цепляться за классы вёрстки."""
    price = None
    match = re.search(r'itemprop="price"[^>]*content="([\d.,]+)"', html, re.I)
    if match:
        price = to_number(match.group(1))

    in_stock = bool(re.search(r'(itemprop="availability"[^>]*(InStock)|'
                              r'"availability"\s*:\s*"[^"]*InStock)', html, re.I))
    if not in_stock:
        in_stock = "в наличии" in html.lower()

    title = ""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if match:
        title = _clean(match.group(1))[:120]

    return {"price": price, "in_stock": in_stock, "title": title}


def scrape(url: str, sku: str, shop: str, currency: str = "RUB") -> tuple[dict, str]:
    """Одна позиция из живого магазина. Возвращает (позиция, статус источника)."""
    got = fetch(url)
    if not got.ok:
        return {}, f"unreachable:{got.reason}"

    # Источник считается живым по факту наличия цены, а не по коду ответа:
    # onlinetrade.ru отдаёт 200 и пустышку, а нормальная витрина может
    # содержать слово captcha в своих же скриптах.
    data = extract_schema_price(got.body)
    if data["price"] is None:
        return {}, f"unreachable:{classify_failure(got.body)}"

    return ({
        "sku": sku,
        "shop": shop,
        "title": data["title"] or sku,
        "price": data["price"],
        "currency": currency,
        "price_status": "listed",
        "in_stock": data["in_stock"],
    }, "ok")
