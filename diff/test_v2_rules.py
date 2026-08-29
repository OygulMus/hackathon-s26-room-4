"""Проверка правил контракта v2 (issue #4) на синтетических данных:
source_status: unreachable, price_status != listed, разошедшаяся валюта.
Запуск: python -m diff.test_v2_rules
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from diff import compute_changes


def check(name, condition):
    status = "OK  " if condition else "FAIL"
    print(f"{status} {name}")
    return condition


def main():
    results = []

    # 1. source_status: unreachable → не пропажа, а "источник недоступен"
    prev = {
        "taken_at": "2026-08-29T10:00:00", "source": "robotshop.com",
        "source_status": "ok",
        "items": {"sku-1": {"shop": "robotshop", "price": 100.0, "currency": "USD", "price_status": "listed", "in_stock": True}},
    }
    curr = {
        "taken_at": "2026-08-30T10:00:00", "source": "robotshop.com",
        "source_status": "unreachable",
        "items": {},
    }
    changes = compute_changes(prev, curr)
    results.append(check(
        "unreachable источник -> source_unreachable, не disappeared",
        len(changes) == 1 and changes[0]["kind"] == "source_unreachable",
    ))

    # 2. price_status: on_request -> цена не сравнивается, не price_change
    prev = {
        "taken_at": "d1", "source_status": "ok",
        "items": {"sku-2": {"price": 90000.0, "currency": "USD", "price_status": "listed", "in_stock": True}},
    }
    curr = {
        "taken_at": "d2", "source_status": "ok",
        "items": {"sku-2": {"price": 90000.0, "currency": "USD", "price_status": "on_request", "in_stock": True}},
    }
    changes = compute_changes(prev, curr)
    results.append(check(
        "price_status=on_request -> price_unavailable, не unchanged/price_change",
        len(changes) == 1 and changes[0]["kind"] == "price_unavailable",
    ))

    # 3. разная валюта -> не считаем дельту молча
    prev = {
        "taken_at": "d1", "source_status": "ok",
        "items": {"sku-3": {"price": 13500.0, "currency": "USD", "price_status": "listed", "in_stock": True}},
    }
    curr = {
        "taken_at": "d2", "source_status": "ok",
        "items": {"sku-3": {"price": 38720.0, "currency": "AUD", "price_status": "listed", "in_stock": True}},
    }
    changes = compute_changes(prev, curr)
    results.append(check(
        "USD -> AUD -> currency_mismatch, не ложный рост в 2.87x",
        len(changes) == 1 and changes[0]["kind"] == "currency_mismatch",
    ))

    # 4. заглушка-цена (одинаковая price_status=listed, но нужно чтобы обычный кейс всё же считался price_change
    prev = {
        "taken_at": "d1", "source_status": "ok",
        "items": {"sku-4": {"price": 100.0, "currency": "USD", "price_status": "listed", "in_stock": True}},
    }
    curr = {
        "taken_at": "d2", "source_status": "ok",
        "items": {"sku-4": {"price": 90.0, "currency": "USD", "price_status": "listed", "in_stock": True}},
    }
    changes = compute_changes(prev, curr)
    results.append(check(
        "листинг -> листинг, обе валюты USD -> обычный price_change считается",
        len(changes) == 1 and changes[0]["kind"] == "price_change" and abs(changes[0]["delta_pct"] - (-10.0)) < 0.01,
    ))

    print(f"\n{sum(results)}/{len(results)} проверок прошло")
    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
