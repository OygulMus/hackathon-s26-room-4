# -*- coding: utf-8 -*-
"""Статическая HTML-страница дайджеста (решение комнаты: выдача — страничка)."""

import html as _html

_CSS = """
:root{--bg:#17151f;--panel:#201d2b;--text:#e8e4f0;--dim:#9a93ab;
--red:#ff5a6a;--warn:#ffc24b;--ok:#5ad19a;--accent:#b49ae8;--line:#332e42}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.55 "JetBrains Mono",ui-monospace,Consolas,monospace;padding:32px 16px}
.wrap{max-width:880px;margin:0 auto}h1{font-size:22px;margin:0 0 4px}
.sub{color:var(--dim);margin-bottom:24px}.chips{display:flex;gap:10px;
flex-wrap:wrap;margin-bottom:24px}.chip{background:var(--panel);
border:1px solid var(--line);border-radius:10px;padding:10px 16px}
.chip b{font-size:20px;display:block}.chip.red b{color:var(--red)}
.chip.warn b{color:var(--warn)}.chip.ok b{color:var(--ok)}
.chip.src b{color:var(--accent)}
.warnbox{border:1px solid var(--warn);color:var(--warn);border-radius:10px;
padding:10px 16px;margin-bottom:24px}
h2{font-size:15px;color:var(--accent);border-bottom:1px solid var(--line);
padding-bottom:6px;margin:28px 0 10px}
ul{list-style:none;padding:0;margin:0}li{padding:8px 12px;border-left:3px solid
var(--line);margin-bottom:6px;background:var(--panel);border-radius:0 8px 8px 0;
overflow-wrap:anywhere}
li.red{border-left-color:var(--red)}li.warn{border-left-color:var(--warn)}
li b{color:var(--warn)}li.red b{color:var(--red)}
.unchanged,.foot{color:var(--dim);margin-top:18px;font-size:13px}
"""


def _line_html(sev, line):
    txt = _html.escape(line)
    while "**" in txt:
        txt = txt.replace("**", "<b>", 1).replace("**", "</b>", 1)
    return f'<li class="{sev}">{txt}</li>'


def to_html(d, title="Мониторинг → дайджест · комната 4"):
    c = d["counts"]
    honest = d["sources_ok"] < d["sources_total"]
    parts = [f"<title>{_html.escape(title)}</title><style>{_CSS}</style>",
             '<div class="wrap">',
             f"<h1>{_html.escape(title)}</h1>",
             f'<div class="sub">{d["date_from"]} → {d["date_to"]} · пороги: '
             f'красный ≥ {d["thresholds"]["red"]:g}%, жёлтый ≥ '
             f'{d["thresholds"]["warn"]:g}% (правило заказчика K4UR)</div>',
             '<div class="chips">',
             f'<div class="chip red"><b>{c["red"]}</b>красных</div>',
             f'<div class="chip warn"><b>{c["warn"]}</b>жёлтых</div>',
             f'<div class="chip ok"><b>{d["unchanged"]}</b>без изменений</div>',
             f'<div class="chip src"><b>{d["sources_ok"]}/{d["sources_total"]}</b>'
             'источников доступно</div>',
             "</div>"]
    if honest:
        parts.append('<div class="warnbox">⚠️ Картина неполная: часть источников '
                     'сегодня не удалось посмотреть — их позиции НЕ считаются '
                     'пропавшими.</div>')
    for source, lines in d["sections"]:
        parts.append(f"<h2>{_html.escape(source or 'источник')}</h2><ul>")
        parts.extend(_line_html(sev, line) for sev, line in lines)
        if not lines:
            parts.append('<li>изменений нет</li>')
        parts.append("</ul>")
    if d["unchanged"]:
        parts.append(f'<div class="unchanged">Без изменений: {d["unchanged"]} '
                     'позиций — свернуто.</div>')
    cs = d.get("cross_shop")
    if cs and cs["rows"]:
        parts.append("<h2>Один товар в разных магазинах (сегодня)</h2><ul>")
        for r in cs["rows"]:
            if r["shops_compared"] < 2:
                continue
            cur = f' {r["currency"]}' if r["currency"] else ""
            parts.append(_line_html("info",
                f'{r["sku"]}: от {r["cheapest"]["price"]:g} ({r["cheapest"]["shop"]}) '
                f'до {r["dearest"]["price"]:g} ({r["dearest"]["shop"]}){cur} — '
                f'разброс **+{r["spread_percent"]:g}%** по {r["shops_compared"]} магазинам'))
        if cs["silent_sources"]:
            parts.append(_line_html("warn",
                f'⚠️ без данных сегодня: {", ".join(cs["silent_sources"])} '
                f'({len(cs["silent_sources"])} из {cs["sources_total"]})'))
        parts.append("</ul>")
    parts.append('<div class="foot">hackathon-s26-room-4 · снимки в data/, '
                 'история — в git</div></div>')
    return "\n".join(parts)
