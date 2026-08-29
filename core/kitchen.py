# -*- coding: utf-8 -*-
"""Дашборд кухни: сканирует departments/, собирает site/index.html.

Карточка отдела: владелец, счётчики изменений по последней паре снимков,
доступность источников, ссылка на страницу отдела (если руководитель её
сделал) либо на сгенерированный дайджест отдела.

Запуск: python -m core.kitchen  [--root .] [--site site]
"""

import argparse
import html as _html
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from core import digest as dg
from core import render
from core.build import pairs_from_dir

_CSS = """
:root{--bg:#17151f;--panel:#201d2b;--text:#e8e4f0;--dim:#9a93ab;
--red:#ff5a6a;--warn:#ffc24b;--ok:#5ad19a;--accent:#b49ae8;--line:#332e42}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.55 "JetBrains Mono",ui-monospace,Consolas,monospace;padding:32px 16px}
.wrap{max-width:960px;margin:0 auto}h1{font-size:24px;margin:0 0 4px}
.sub{color:var(--dim);margin-bottom:28px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
a.card{display:block;background:var(--panel);border:1px solid var(--line);
border-radius:14px;padding:18px;text-decoration:none;color:var(--text);
transition:border-color .15s}
a.card:hover{border-color:var(--accent)}a.card.empty{opacity:.55}
.emoji{font-size:30px}.title{font-weight:bold;margin:8px 0 2px}
.owner{color:var(--accent);font-size:13px;margin-bottom:10px}
.stat{font-size:13px;color:var(--dim)}.stat b.red{color:var(--red)}
.stat b.warn{color:var(--warn)}.stat b.ok{color:var(--ok)}
.digest-link{display:inline-block;margin-top:26px;color:var(--accent)}
.foot{color:var(--dim);margin-top:34px;font-size:13px;border-top:1px solid
var(--line);padding-top:14px}
"""


def dept_summary(dept_dir):
    """-> (pairs, counts, sources_ok, sources_total, last_date, n_items)"""
    data = dept_dir / "data"
    if not data.is_dir():
        return None
    pairs = pairs_from_dir(data)
    if not pairs:
        snaps = [p for p in data.glob("*.json")]
        return {"pairs": [], "n_snaps": len(snaps)}
    d = dg.build_digest(pairs)
    n_items = sum(len(b["items"]) for _, b, _ in pairs)
    return {"pairs": pairs, "digest": d, "n_items": n_items,
            "n_snaps": len(list(data.glob("*.json")))}


def build_site(root=".", site="site"):
    root, site_dir = pathlib.Path(root), pathlib.Path(root, site)
    site_dir.mkdir(parents=True, exist_ok=True)
    cards, all_pairs = [], []

    for dept_json in sorted(root.glob("departments/*/dept.json")):
        dept_dir = dept_json.parent
        meta = json.loads(dept_json.read_text(encoding="utf-8"))
        s = dept_summary(dept_dir)

        own_page = dept_dir / "index.html"
        href, cls, stat = None, "empty", "ждёт первых снимков"
        if s and s.get("pairs"):
            all_pairs.extend(s["pairs"])
            d = s["digest"]
            c = d["counts"]
            stat = (f'позиции: {s["n_items"]} · изменения: '
                    f'<b class="red">{c["red"]}🔴</b> <b class="warn">{c["warn"]}🟡</b>'
                    f' · источники: <b class="ok">{d["sources_ok"]}/{d["sources_total"]}</b>'
                    f'<br>снимки: {s["n_snaps"]} · {d["date_from"]} → {d["date_to"]}')
            cls = ""
            page = site_dir / f'dept-{meta["code"]}.html'
            page.write_text(render.to_html(
                d, title=f'{meta["emoji"]} {meta["title"]} · {meta["owner"]}'),
                encoding="utf-8")
            href = page.name
        elif s and s.get("n_snaps"):
            stat = f'снимков: {s["n_snaps"]} — нужен второй для сравнения'
        if own_page.exists():
            href = "../" + own_page.relative_to(root).as_posix()
            cls = ""
            stat += " · своя страница ↗"

        cards.append(
            f'<a class="card {cls}" {"href=" + chr(34) + href + chr(34) if href else ""}>'
            f'<div class="emoji">{meta["emoji"]}</div>'
            f'<div class="title">{_html.escape(meta["title"])}</div>'
            f'<div class="owner">{_html.escape(meta["owner"])}</div>'
            f'<div class="stat">{stat}</div></a>')

    digest_link = ""
    if all_pairs:
        d_all = dg.build_digest(all_pairs)
        (site_dir / "digest.html").write_text(
            render.to_html(d_all, title="Общий дайджест кухни"), encoding="utf-8")
        (site_dir / "digest.md").write_text(dg.to_markdown(d_all), encoding="utf-8")
        digest_link = '<a class="digest-link" href="digest.html">→ общий дайджест кухни</a>'

    page = (f"<title>Кухня · комната 4</title><style>{_CSS}</style>"
            '<div class="wrap"><h1>🍽 Кухня · комната 4</h1>'
            '<div class="sub">мониторинг цен закупки по отделам · заказчик: Айгуль ·'
            ' пороги: 🔴 ≥10% · 🟡 ≥5%</div>'
            f'<div class="grid">{"".join(cards)}</div>{digest_link}'
            '<div class="foot">hackathon-s26-room-4 · «Чужая боль» 29.08.2026 ·'
            ' снимки в departments/*/data, история — в git</div></div>')
    (site_dir / "index.html").write_text(page, encoding="utf-8")
    return site_dir / "index.html"


def main(argv=None):
    ap = argparse.ArgumentParser(description="собрать дашборд кухни")
    ap.add_argument("--root", default=".")
    ap.add_argument("--site", default="site")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    out = build_site(args.root, args.site)
    print(f"дашборд собран: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
