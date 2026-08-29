# -*- coding: utf-8 -*-
"""Сборка дайджеста из событий диффа.

Пороги подсветки — правило заказчика K4UR (Айгуль, рестораны):
рост >= RED_PCT — красный флаг (искать поставщика / стоп продажи),
рост >= WARN_PCT — жёлтый. Настраиваются параметрами.
"""

RED_PCT = 10.0
WARN_PCT = 5.0

_ORDER = {"price_change": 0, "back_in_stock": 1, "out_of_stock": 2,
          "gone": 3, "new_item": 4, "not_comparable": 5, "source_unreachable": 6}


def severity(ev, red=RED_PCT, warn=WARN_PCT):
    if ev["type"] == "price_change" and ev["pct"] >= red:
        return "red"
    if ev["type"] == "price_change" and ev["pct"] >= warn:
        return "warn"
    if ev["type"] in ("source_unreachable", "gone", "out_of_stock"):
        return "warn"
    return "info"


def _fmt_price(v):
    if v is None:
        return "?"
    s = f"{v:,.0f}" if float(v) == int(v) else f"{v:,.2f}"
    return s.replace(",", " ")


def _fmt_pct(pct):
    sign = "+" if pct > 0 else "−"
    return f"{sign}{abs(pct):.1f}%"


def event_line(ev):
    t = ev["type"]
    if t == "price_change":
        arrow = "↑" if ev["pct"] > 0 else "↓"
        return (f'{ev["sku"]}: {_fmt_price(ev["from"])} → {_fmt_price(ev["to"])}, '
                f'**{_fmt_pct(ev["pct"])}** {arrow}')
    if t == "back_in_stock":
        note = f' ({ev["note"]})' if ev.get("note") else ""
        return f'{ev["sku"]}: **появился в наличии**{note}'
    if t == "out_of_stock":
        return f'{ev["sku"]}: **пропал из наличия**'
    if t == "gone":
        return f'{ev["sku"]}: **пропал из выдачи** (не путать со снижением цены)'
    if t == "new_item":
        return f'{ev["sku"]}: **новая позиция**, {_fmt_price(ev.get("to"))}'
    if t == "not_comparable":
        return f'{ev["sku"]}: цена не сравнивается ({ev.get("note", "")})'
    if t == "source_unreachable":
        return f'источник **{ev["title"]}**: недоступен, позиции не считаются пропавшими'
    return f'{ev["sku"]}: {t}'


def build_digest(pairs, red=RED_PCT, warn=WARN_PCT):
    """pairs: list[(snap_a, snap_b, events)] по одному на источник.

    -> {"date_from", "date_to", "sections": [(source, [(severity, line)])],
        "unchanged", "sources_total", "sources_ok", "counts"}
    """
    sections, unchanged = [], 0
    sources_ok = 0
    counts = {"red": 0, "warn": 0, "info": 0}
    date_from = date_to = ""

    for a, b, events in pairs:
        date_from, date_to = a["date"] or date_from, b["date"] or date_to
        if b.get("source_status") != "unreachable":
            sources_ok += 1
            touched = {e["sku"] for e in events if e["sku"]}
            unchanged += sum(1 for sku in b["items"] if sku not in touched)
        lines = []
        for ev in sorted(events, key=lambda e: (_ORDER.get(e["type"], 9),
                                                -abs(e.get("pct") or 0))):
            sev = severity(ev, red, warn)
            counts[sev] += 1
            lines.append((sev, event_line(ev)))
        sections.append((b.get("source", "") or a.get("source", ""), lines))

    return {"date_from": date_from, "date_to": date_to, "sections": sections,
            "unchanged": unchanged, "sources_total": len(pairs),
            "sources_ok": sources_ok, "counts": counts,
            "thresholds": {"red": red, "warn": warn}}


def plural_ru(n, one, few, many):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def to_markdown(d):
    out = [f'# Дайджест изменений ({d["date_from"]} → {d["date_to"]})', ""]
    out.append(f'Источники: доступно **{d["sources_ok"]} из {d["sources_total"]}**.'
               + (" ⚠️ картина неполная!" if d["sources_ok"] < d["sources_total"] else ""))
    out.append(f'Пороги подсветки: 🔴 ≥ {d["thresholds"]["red"]:g}% · '
               f'🟡 ≥ {d["thresholds"]["warn"]:g}% (правило заказчика K4UR)')
    out.append("")
    badge = {"red": "🔴 ", "warn": "🟡 ", "info": ""}
    for source, lines in d["sections"]:
        if len(d["sections"]) > 1:
            out.append(f'## {source or "источник"}')
    # секции с одним источником — без заголовка
        for sev, line in lines:
            out.append(f"- {badge[sev]}{line}")
        out.append("")
    if d["unchanged"]:
        w = plural_ru(d["unchanged"], "позиция", "позиции", "позиций")
        out.append(f'Без изменений: {d["unchanged"]} {w} — свернуто.')
    return "\n".join(out).rstrip() + "\n"
