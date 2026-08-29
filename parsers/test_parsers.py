"""Приёмка модуля parsers. Источник истины — examples/02-парсинг-вёрстки/expected.md.

Ключевые проверки оттуда:
  NBSP в цене не ломает число; «цена-old» не взята за текущую;
  «ожидается» прочитано как отсутствие.
"""

from pathlib import Path

from parsers.cards import parse_card
from parsers.snapshot import build_snapshot

REPO = Path(__file__).resolve().parents[1]
CARDS = REPO / "examples" / "02-парсинг-вёрстки" / "input"


def card(name):
    return (CARDS / name).read_text(encoding="utf-8")


def test_card_a_sku_from_title_parentheses():
    assert parse_card(card("card-a.html"))["sku"] == "MZ7L3960HCJR-00A07"


def test_card_a_takes_the_current_price_not_the_struck_out_one():
    """33 900 зачёркнута, текущая — 32 100."""
    assert parse_card(card("card-a.html"))["price"] == 32100.0


def test_card_a_nbsp_does_not_break_the_number():
    raw = card("card-a.html")
    assert " " in raw or "&nbsp;" in raw
    assert parse_card(raw)["price"] == 32100.0


def test_card_a_is_in_stock():
    assert parse_card(card("card-a.html"))["in_stock"] is True


def test_card_b_sku_from_data_attribute():
    assert parse_card(card("card-b.html"))["sku"] == "ST16000NM004J"


def test_card_b_price():
    assert parse_card(card("card-b.html"))["price"] == 42200.0


def test_card_b_awaiting_delivery_means_not_in_stock():
    """«Ожидается поставка» = нет в наличии, а не «есть»."""
    assert parse_card(card("card-b.html"))["in_stock"] is False


def test_price_status_is_listed_when_there_is_a_real_price():
    assert parse_card(card("card-a.html"))["price_status"] == "listed"


def test_placeholder_price_is_marked_on_request():
    """Заглушка «цена по запросу» не должна попасть в сравнение как число."""
    html = '<div><a class="title">Робот (ABC-1)</a>' \
           '<span class="price-new">Цена по запросу</span></div>'
    item = parse_card(html)
    assert item["price"] is None
    assert item["price_status"] == "on_request"


def test_snapshot_matches_contract_v2():
    items = [parse_card(card("card-a.html")), parse_card(card("card-b.html"))]
    snap = build_snapshot("shop.example", items)
    assert snap["source_status"] == "ok"
    assert set(snap["items"]) == {"MZ7L3960HCJR-00A07", "ST16000NM004J"}
    one = snap["items"]["MZ7L3960HCJR-00A07"]
    assert set(one) >= {"shop", "title", "price", "currency",
                        "price_status", "in_stock"}
    assert one["currency"] == "RUB"


def test_unreachable_source_yields_no_items_but_says_why():
    """403/капча/пустая заглушка — это НЕ «все позиции пропали»."""
    snap = build_snapshot("kns.ru", [], status="unreachable")
    assert snap["source_status"] == "unreachable"
    assert snap["items"] == {}


def test_core_reads_our_snapshot_without_an_adapter():
    from core.snapshot import normalize

    snap = build_snapshot("shop.example", [parse_card(card("card-a.html"))])
    norm = normalize(snap)
    assert norm["items"]["MZ7L3960HCJR-00A07"]["price"] == 32100.0
    assert norm["source_status"] == "ok"


def test_schema_price_is_extracted_without_network():
    from parsers.shops import extract_schema_price

    html = ('<title>SSD Samsung PM1653</title>'
            '<meta itemprop="price" content="702596" />'
            '<link itemprop="availability" href="https://schema.org/InStock" />')
    got = extract_schema_price(html)
    assert got["price"] == 702596.0
    assert got["in_stock"] is True


def test_tiny_body_counts_as_unreachable_even_with_http_200():
    """onlinetrade.ru отвечает 200 и отдаёт пустышку — самый опасный отказ."""
    from parsers.shops import MIN_REAL_PAGE_BYTES

    assert MIN_REAL_PAGE_BYTES > 10_000


def test_captcha_page_is_not_a_price_page():
    from parsers.shops import CAPTCHA_MARKERS

    kns = "запросы, поступившие с вашего IP-адреса, похожи на автоматические"
    assert any(m in kns.lower() for m in CAPTCHA_MARKERS)
