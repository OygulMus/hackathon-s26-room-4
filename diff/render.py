"""Рендер списка изменений (diff.engine.compute_changes) в markdown-дайджест."""


def _fmt_price(value):
    if value is None:
        return "—"
    if float(value).is_integer():
        text = f"{int(value):,}"
    else:
        text = f"{value:,.2f}"
    return text.replace(",", " ")


def _fmt_pct(delta_pct):
    sign = "+" if delta_pct >= 0 else "−"
    return f"{sign}{abs(delta_pct):.1f}%"


def _line(change):
    kind = change["kind"]
    sku = change["sku"]
    currency = f" {change['currency']}" if change.get("currency") else ""

    if kind == "price_change":
        arrow = "↑" if change["delta_pct"] >= 0 else "↓"
        return (
            f"- {sku}: {_fmt_price(change['prev_price'])} → "
            f"{_fmt_price(change['curr_price'])}{currency}, "
            f"**{_fmt_pct(change['delta_pct'])}** {arrow}"
        )
    if kind == "appeared":
        return f"- {sku}: **появился в наличии** (цена без изменений)"
    if kind == "went_out_of_stock":
        return (
            f"- {sku}: **нет в наличии** (в выдаче остался, цена "
            f"{_fmt_price(change['last_price'])}{currency}; не путать с пропажей "
            f"из выдачи)"
        )
    if kind == "disappeared":
        return f"- {sku}: **пропал из выдачи** (не путать со снижением цены)"
    if kind == "new":
        if change.get("price_status", "listed") == "listed":
            price_text = _fmt_price(change["price"]) + currency
        else:
            price_text = "цена по запросу"
        return f"- {sku}: **новая позиция**, {price_text}"
    if kind == "source_unreachable":
        return f"- {sku}: источник недоступен, сравнение пропущено (не пропажа)"
    if kind == "currency_mismatch":
        return (
            f"- {sku}: валюта изменилась ({change['prev_currency']} → "
            f"{change['curr_currency']}), сравнение цены не выполнено"
        )
    if kind == "price_unavailable":
        return (
            f"- {sku}: цена недоступна ({change['price_status']}), "
            f"сравнение не выполнено"
        )
    raise ValueError(f"неизвестный тип изменения: {kind}")


def render_digest(prev_label, curr_label, changes):
    """changes — результат diff.engine.compute_changes. Возвращает markdown-текст."""
    notable = [c for c in changes if c["kind"] != "unchanged"]
    unchanged = [c for c in changes if c["kind"] == "unchanged"]

    lines = [f"# Дайджест изменений ({prev_label} → {curr_label})", ""]

    if not notable:
        lines.append("Изменений нет.")
    else:
        for change in sorted(notable, key=lambda c: c["sku"]):
            lines.append(_line(change))

    if unchanged:
        word = "позиция" if len(unchanged) == 1 else (
            "позиции" if 2 <= len(unchanged) % 10 <= 4 and not (11 <= len(unchanged) % 100 <= 14) else "позиций"
        )
        lines.append(f"- Остальные {len(unchanged)} {word}: без изменений")

    return "\n".join(lines) + "\n"
