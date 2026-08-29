#!/usr/bin/env python3
"""PQQM: КленМаркет -> снимок цен в контракте v2.

Использование:
  python3 departments/oborudovanie/collect.py
  python3 departments/oborudovanie/collect.py --out-dir /tmp/snapshots

Каталог отделён от кода: новые позиции добавляются в catalog.json.
Неуспешный запрос не подменяется пустой ценой: создаётся снимок со статусом
source_status=unreachable.
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
PRICE_RE = re.compile(
    r'<span[^>]*class="price__current-value"[^>]*itemprop="price"[^>]*content="([0-9]+)"'
)
IN_STOCK_RE = re.compile(r'itemprop="availability"[^>]*InStock', re.IGNORECASE)


def fetch_html(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (PQQM price monitor)"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_klenmarket(html, item, shop):
    match = PRICE_RE.search(html)
    if not match:
        return {
            "shop": shop,
            "title": item["title"],
            "price": None,
            "currency": "RUB",
            "price_status": "on_request",
            "in_stock": False,
        }
    return {
        "shop": shop,
        "title": item["title"],
        "price": float(match.group(1)),
        "currency": "RUB",
        "price_status": "listed",
        "in_stock": bool(IN_STOCK_RE.search(html)),
    }


def collect_source(source_config, taken_at):
    snapshot = {
        "taken_at": taken_at,
        "source": source_config["source"],
        "source_status": "ok",
        "items": {},
    }
    try:
        for item in source_config["items"]:
            if source_config["adapter"] != "klenmarket":
                raise ValueError(f'неизвестный адаптер: {source_config["adapter"]}')
            html = fetch_html(item["url"])
            snapshot["items"][item["sku"]] = parse_klenmarket(
                html, item, source_config["shop"]
            )
    except Exception as error:
        snapshot["source_status"] = "unreachable"
        snapshot["items"] = {}
        snapshot["error"] = f"{type(error).__name__}: {error}"
    return snapshot


def main():
    parser = argparse.ArgumentParser(description="PQQM: собрать снимок КленМаркет")
    parser.add_argument("--catalog", type=Path, default=HERE / "catalog.json")
    parser.add_argument("--out-dir", type=Path, default=HERE / "data")
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    taken_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for source_config in catalog["sources"]:
        snapshot = collect_source(source_config, taken_at)
        safe_source = re.sub(r"[^a-z0-9]+", "-", snapshot["source"].lower()).strip("-")
        safe_time = taken_at.replace(":", "-").replace("+", "plus")
        path = args.out_dir / f"snapshot-{safe_time}-{safe_source}.json"
        path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
