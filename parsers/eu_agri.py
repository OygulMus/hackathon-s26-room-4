"""Открытые цены Еврокомиссии: мясо, птица, свинина, молоко, сахар.

Почему это важнее остальных источников: здесь есть **недельная история**.
Магазины дают только «сегодня», и первый снимок сравнивать не с чем. Здесь
каждая неделя — готовый снимок, поэтому дайджест показывает настоящее
изменение, а не «изменений нет».

Ключ и регистрация не нужны:

    https://www.ec.europa.eu/agrifood/api/<товар>/prices?memberStateCodes=HR&years=2026

Проверено 29.08.2026: работают `poultry`, `beef`, `pigmeat`, `sugar`,
`rawMilk`. Эндпоинтов `eggs`, `cereals`, `fruitAndVegetable` нет — отвечают 404.
"""

from __future__ import annotations

import json
import re
import urllib.request
from collections import defaultdict
from datetime import datetime

from parsers.snapshot import build_snapshot

BASE = "https://www.ec.europa.eu/agrifood/api"
PRODUCTS = ("poultry", "beef", "pigmeat", "sugar", "rawMilk")


def fetch_series(product: str, country: str = "HR", year: int = 2026) -> list[dict]:
    url = f"{BASE}/{product}/prices?memberStateCodes={country}&years={year}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8", "ignore"))


def _price(raw: str) -> float | None:
    digits = re.sub(r"[^\d.]", "", str(raw or ""))
    return float(digits) if digits else None


def _sku(record: dict) -> str:
    name = (record.get("productName") or "").strip()
    return re.sub(r"\s+", "-", name.lower()) or "unknown"


def snapshots_by_week(records: list[dict], source: str) -> list[dict]:
    """Недельные записи → снимки контракта v2, по одному на неделю.

    Каждый снимок помечен датой конца недели, поэтому `core/` берёт два
    последних и сравнивает их между собой без единой правки.
    """
    weeks: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        end = record.get("endDate") or ""
        try:
            taken = datetime.strptime(end, "%d/%m/%Y")
        except ValueError:
            continue
        price = _price(record.get("price"))
        weeks[taken.isoformat(timespec="seconds")].append({
            "sku": _sku(record),
            "shop": source,
            "title": f'{record.get("productName", "")} '
                     f'({record.get("unit", "")})'.strip(),
            "price": price,
            "currency": "EUR",
            "price_status": "listed" if price is not None else "unknown",
            "item_status": "ok" if price is not None else "not_found",
            "in_stock": price is not None,
        })

    return [build_snapshot(source, items, taken_at=taken)
            for taken, items in sorted(weeks.items())]


def latest_pair(product: str, country: str = "HR", year: int = 2026) -> list[dict]:
    """Два последних недельных снимка — ровно то, что ест `core/`."""
    source = f"ec.europa.eu/{product}"
    return snapshots_by_week(fetch_series(product, country, year), source)[-2:]


def main(argv: list[str]) -> int:
    """CLI: сложить недельные снимки в папку отдела.

    python3 -m parsers.eu_agri departments/myaso/data poultry beef pigmeat
    """
    import sys
    from pathlib import Path

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    args = argv[1:]
    if not args:
        print("использование: python3 -m parsers.eu_agri <папка> [товары...]",
              file=sys.stderr)
        return 2

    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)
    products = args[1:] or list(PRODUCTS)

    for product in products:
        try:
            pair = latest_pair(product)
        except Exception as exc:
            print(f"  {product:<10} источник недоступен: {type(exc).__name__}")
            continue
        if len(pair) < 2:
            print(f"  {product:<10} меньше двух недель — сравнивать не с чем")
            continue

        for snap in pair:
            week = snap["taken_at"][:10]
            (out / f"{week}-eu-{product}.json").write_text(
                json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")

        before, after = pair
        print(f"  {product:<10} {before['taken_at'][:10]} → {after['taken_at'][:10]}"
              f"  позиций {len(after['items'])}")
        for sku, item in after["items"].items():
            was = before["items"].get(sku, {}).get("price")
            now = item["price"]
            if was and now:
                print(f"      {sku:<22} {was:>8.2f} → {now:>8.2f} "
                      f"{(now / was - 1) * 100:+6.1f}%")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv))
