# core/ — оркестратор: снимки → дайджест (SQSU)

Issue #8. Склеивает снимки источников в дайджест изменений: markdown + статическая
HTML-страница (решение комнаты: выдача — страничка).

## Запуск

```bash
# приёмочный пример 01
python -m core.build --pair "examples/01-снимки-цен/input/snapshot-2026-08-27.json" \
                     "examples/01-снимки-цен/input/snapshot-2026-08-28.json"

# рабочий режим: папка со снимками, группировка по source,
# внутри источника сравниваются два последних по дате
python -m core.build --data data/snapshots --out-dir site
```

Выход: `out/digest.md` и `out/index.html` (папка настраивается `--out-dir`).
Пороги подсветки: `--red 10 --warn 5` (по умолчанию правило заказчика K4UR:
рост ≥10% — красный флаг, ≥5% — жёлтый).

## Контракт снимка (v2, issue #4)

```json
{"taken_at": "ISO-8601", "source": "домен", "source_status": "ok|unreachable",
 "items": {"sku": {"shop": "...", "title": "...", "price": 13500.0,
   "currency": "USD", "price_status": "listed|on_request|unknown", "in_stock": true}}}
```

`core/snapshot.py` также понимает v1 из `examples/01` (плоский `{date, items}`)
и `items` списком (как в `docs/evidence-4NNT/`).

Правила честности (issue #4 + PR #9):

- `source_status: unreachable` → позиции источника НЕ считаются пропавшими,
  в дайджесте строка «источник недоступен» и счётчик «доступно N из M»;
- `price_status != listed` → цена в сравнение не идёт (заглушки 100000 /
  «Contact us» не рождают фальшивых обвалов);
- цены сравниваются только внутри одной валюты, конвертации нет.

## Интеграция с модулями комнаты

- **diff/ (issue #5):** core импортирует `diff.engine.diff_snapshots(a, b)`,
  если модуль существует; пока его нет — работает `core/fallback_diff.py`
  (удалим при мерже diff/). Интерфейс события описан в `fallback_diff.py`.
- **parsers/ (issue #6):** кладёт снимки в `data/snapshots/` в контракте v2 —
  ничего больше не нужно.
- **timelog/ (issue #7):** секция времени подключается в `render.py` отдельным
  блоком (место помечено), критерий 4NNT — обе цифры с порогами.
