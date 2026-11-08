"""Self-contained HTML report (a single file, opens with a double click or from a phone)."""
from __future__ import annotations

import html
import json
from datetime import datetime

from . import quality
from .i18n import lang, money, original_price, t
from .rules import Rules

CSS = """
:root{--bg:#f6f5f2;--card:#fff;--ink:#1d1d1f;--muted:#6b6b70;--line:#e4e2dc;--accent:#0b6e4f;
--warn:#a15c00;--chip:#efede7;--lvl-esatto:#0b6e4f;--lvl-superiore:#3a4bd1;--lvl-simile:#7a5c00;--bad:#a13a2a}
@media (prefers-color-scheme:dark){:root{--bg:#141416;--card:#1d1d20;--ink:#ececef;--muted:#9a9aa2;
--line:#2c2c31;--accent:#3ccf91;--warn:#f0b35a;--chip:#26262b;--lvl-esatto:#3ccf91;
--lvl-superiore:#8d9bff;--lvl-simile:#e3c25c;--bad:#ff8a78}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 16px 60px}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.01em}.sub{color:var(--muted);margin:0 0 22px}
.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:26px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.tile .k{color:var(--muted);font-size:12.5px}.tile .v{font-size:20px;font-weight:650;font-variant-numeric:tabular-nums}
.tile.total{background:var(--accent);color:#fff;border-color:transparent}.tile.total .k{color:#ffffffcc}
@media (prefers-color-scheme:dark){.tile.total{color:#0d1f17}.tile.total .k{color:#0d1f17bb}}
section.comp{background:var(--card);border:1px solid var(--line);border-radius:14px;margin:0 0 18px;overflow:hidden}
.head{display:flex;gap:16px;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.head h2{font-size:17px;margin:0}.head .best{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums}
.head .delta{font-size:12.5px;color:var(--muted)}.spark{color:var(--accent)}
table{width:100%;border-collapse:collapse}td,th{padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{font-size:12px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:0}td.p{font-weight:650;white-space:nowrap;font-variant-numeric:tabular-nums}
td.p small{display:block;font-weight:400;color:var(--muted);font-size:12px}
a{color:inherit}a:hover{color:var(--accent)}.t{max-width:420px}.t a{text-decoration:none;border-bottom:1px solid var(--line)}
.lvl{display:inline-block;white-space:nowrap;font-size:11.5px;font-weight:650;border:1px solid currentColor;border-radius:999px;padding:1px 8px;margin:0 0 4px}
.lvl.incerto{color:var(--muted)}.lvl.esatto{color:var(--lvl-esatto)}.lvl.superiore{color:var(--lvl-superiore)}.lvl.simile{color:var(--lvl-simile)}
.model{font-size:13px;color:var(--muted)}.chip{display:inline-block;background:var(--chip);border-radius:6px;padding:1px 7px;font-size:12px;margin:2px 4px 0 0}
.rel{display:block;font-size:12px;font-weight:600;margin-top:4px}.rel.alta{color:var(--lvl-esatto)}.rel.media{color:var(--warn)}.rel.bassa{color:var(--bad)}
.w{display:block;color:var(--warn);font-size:12.5px}.empty{padding:16px;color:var(--muted)}
.src td{font-size:13.5px}.bad{color:var(--bad);font-weight:600}.okc{color:var(--accent);font-weight:600}
.scroll{overflow-x:auto}
details.more summary{padding:12px 16px;cursor:pointer;color:var(--muted)}
details.more table{border-top:1px solid var(--line)}
@media (max-width:700px){.t{max-width:220px}td,th{padding:8px}
table.offers thead{display:none}table.offers tr{display:block;padding:10px 12px;border-bottom:1px solid var(--line)}
table.offers td{display:block;padding:2px 0;border:0;max-width:none}.wrap{padding-top:16px}}
"""


def _e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _spark(cfg, points: list[tuple[str, float]]) -> str:
    if len(points) < 2:
        return ""
    vals = [p[1] for p in points]
    lo, hi = min(vals), max(vals)
    w, h = 140, 34
    rng = (hi - lo) or 1
    xy = [(i * (w - 4) / (len(vals) - 1) + 2, h - 3 - (v - lo) / rng * (h - 6)) for i, v in enumerate(vals)]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    title = f"{points[0][0]} → {points[-1][0]}: {money(cfg, vals[0])} → {money(cfg, vals[-1])}"
    return (f'<svg class="spark" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{_e(title)}">'
            f'<title>{_e(title)}</title><polyline fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linejoin="round" points="{pts}"/><circle cx="{xy[-1][0]:.1f}" cy="{xy[-1][1]:.1f}" r="3" '
            f'fill="currentColor"/></svg>')


def telegram_summary(cfg: dict, store) -> str:
    """End-of-run message: the most reliable offer for each product and, if lower, the price to verify."""
    rules = Rules(cfg)
    run = store.last_run()
    offers = quality.assess(store.offers_of_run(run["id"]), cfg)  # already sorted by total
    total, missing, blocks = 0.0, 0, []
    for cid in rules.components:
        name = _e(rules.name(cid))
        offs = [o for o in offers if o["component"] == cid]
        best = quality.pick(offs)
        if best is None:
            missing += 1
            blocks.append(f"<b>{name}</b>: {t(cfg, 'tg.none')}")
            continue
        total += best["total"]
        label = "" if best["level"] == "esatto" else f" · {t(cfg, 'level.' + best['level'])}"
        if original_price(cfg, best):
            label += f" · {t(cfg, 'tg.from', orig=original_price(cfg, best))}"
        label += f" · {t(cfg, 'rel.' + best['affidabilita'])}"
        lines = [f"<b>{name}: {money(cfg, best['total'])}</b>{_e(label)}",
                 f'<a href="{_e(best["url"])}">{_e(best["title"][:70])}</a> · {_e(best["shop"])}']
        lines += [f"⚠ {_e(w)}" for w in best["warnings"][:1]]
        low = next((o for o in offs if o["level"] != "incerto"), offs[0])
        if low["total"] < best["total"]:
            why = "; ".join(low["warnings"]) or t(cfg, f"level.{low['level']}")
            lines.append(f'{t(cfg, "tg.low")} <a href="{_e(low["url"])}">{money(cfg, low["total"])}</a> · {_e(low["shop"])} · {t(cfg, "rel." + low["affidabilita"])}: {_e(why)}')
        blocks.append("\n".join(lines))
    ts = datetime.fromisoformat(run["ts"])
    head = t(cfg, "tg.head", when=f"{ts:%H:%M}") + "\n"
    head += t(cfg, "tg.partial", n=missing, price=money(cfg, total)) if missing else t(cfg, "tg.total", price=money(cfg, total))
    return "\n\n".join([head, *blocks])


def _source_state(cfg, st: dict) -> str:
    if st.get("stato") == "browser":
        return f'<span class="bad">{t(cfg, "report.browser")}</span>'
    if st.get("stato") == "currency":
        return f'<span class="bad">{t(cfg, "report.currency")}</span>'
    if st.get("saltate") and not st["ok"]:
        return f'<span class="bad">{t(cfg, "report.stopped")}</span>'
    if st["ok"] and st["trovati"] == 0:
        return f'<span class="bad">{t(cfg, "report.zero")}</span>'
    if st["ok"] and not st["bloccate"] and not st["errori"]:
        return f'<span class="okc">{t(cfg, "report.ok")}</span>'
    if st["bloccate"] and not st["ok"]:
        return f'<span class="bad">{t(cfg, "report.blocked")}</span>'
    return f'<span class="bad">{t(cfg, "report.errors")}</span>' if not st["ok"] else t(cfg, "report.partial_src")


def generate(cfg: dict, store, path: str) -> str:
    rules = Rules(cfg)
    run = store.last_run()
    if run is None:
        raise SystemExit("No run saved yet")
    offers = quality.assess(store.offers_of_run(run["id"]), cfg)
    stats = json.loads(run["sources"] or "{}")
    nshow = int(cfg.get("generale", {}).get("offerte_per_prodotto", 8))
    ts = datetime.fromisoformat(run["ts"])
    head = t(cfg, "report.head")

    def table(body):
        return ('<div class="scroll"><table class="offers"><thead><tr>' + "".join(f"<th>{_e(h)}</th>" for h in head) +
                f'</tr></thead><tbody>{"".join(body)}</tbody></table></div>')

    tiles, sections, total, missing = [], [], 0.0, []
    for cid in rules.components:
        offs = [o for o in offers if o["component"] == cid]
        name = rules.name(cid)
        if not offs:
            missing.append(name)
            tiles.append(f'<div class="tile"><div class="k">{_e(name)}</div><div class="v">—</div></div>')
            sections.append(f'<section class="comp"><div class="head"><h2>{_e(name)}</h2></div>'
                            f'<div class="empty">{t(cfg, "report.none")}</div></section>')
            continue
        best = quality.pick(offs)
        total += best["total"]
        prev = store.min_before(cid, run["id"])
        delta = ""
        if prev is not None:
            d = best["total"] - prev
            delta = ("▼ " if d < 0 else "▲ " if d > 0 else "= ") + t(cfg, "report.delta", price=money(cfg, abs(d)))
        low = next((o for o in offs if o["level"] != "incerto"), offs[0])
        low_note = t(cfg, "report.low", price=money(cfg, low["total"])) if low["total"] < best["total"] else ""
        tiles.append(f'<div class="tile"><div class="k">{_e(name)}</div><div class="v">{money(cfg, best["total"])}</div></div>')
        rows = []
        # shops with no customs first: distant ones, which cost more than they seem to, must not fill the top of the list
        for o in sorted(offs, key=lambda x: (x["level"] == "incerto", bool((x.get("extra") or {}).get("dogana")), x["total"])):
            ship = (t(cfg, "ship.free") if o["shipping"] == 0
                    else t(cfg, "ship.plus", price=money(cfg, o["shipping"])) if o["shipping"] else t(cfg, "ship.na"))
            notes = f'<span class="chip">{t(cfg, "report.pick")}</span>' if o is best else ""
            notes += "".join(f'<span class="chip">{_e(x)}</span>' for x in o["tags"])
            if o.get("stesso_modello"):
                notes += f'<span class="chip">{_e(t(cfg, "report.same_model", n=o["stesso_modello"][0], price=money(cfg, o["stesso_modello"][1])))}</span>'
            notes += "".join(f'<span class="w">⚠ {_e(w)}</span>' for w in o["warnings"])
            rows.append(
                f'<tr><td class="p">{"≈ " if original_price(cfg, o) else ""}{money(cfg, o["total"])}<small>{money(cfg, o["price"])} · {ship}</small></td>'
                f'<td><span class="lvl {_e(o["level"])}">{_e(t(cfg, "level." + o["level"]))}</span>'
                f'<div class="model">{_e(o["model"])}</div>'
                f'<span class="rel {o["affidabilita"]}">{_e(t(cfg, "rel." + o["affidabilita"]))}</span></td>'
                f'<td class="t"><a href="{_e(o["url"])}" target="_blank" rel="noopener">{_e(o["title"][:160])}</a></td>'
                f'<td>{_e(o["shop"])}<div class="model">{_e(o["source"])}</div></td><td>{notes}</td></tr>')
        more = (f'<details class="more"><summary>{t(cfg, "report.more", n=len(offs) - nshow)}</summary>'
                f'{table(rows[nshow:])}</details>') if len(offs) > nshow else ""
        n_out, out_rows = store.discarded_of_run(run["id"], cid)
        if n_out:
            out_head = "".join(f"<th>{_e(h)}</th>" for h in t(cfg, "report.discarded_head"))
            out_body = "".join(f'<tr><td class="t">{_e(r["title"][:120])}</td><td class="p">{money(cfg, r["price"])}</td><td>{_e(r["source"])}</td><td class="model">{_e(r["reason"])}</td></tr>' for r in out_rows)
            more += (f'<details class="more"><summary>{t(cfg, "report.discarded", n=n_out)}</summary><div class="scroll"><table>'
                     f'<thead><tr>{out_head}</tr></thead><tbody>{out_body}</tbody></table></div></details>')
        sections.append(
            f'<section class="comp"><div class="head"><div><h2>{_e(name)}</h2><div class="delta">{_e(delta)}</div>'
            f'<div class="delta">{_e(low_note)}</div></div>'
            f'<div style="display:flex;gap:14px;align-items:center">{_spark(cfg, store.daily_min(cid))}<div class="best">{money(cfg, best["total"])}</div></div></div>'
            f'{table(rows[:nshow])}{more}</section>')

    src_rows = []
    for sid, st in sorted(stats.items()):
        src_rows.append(f'<tr><td>{_e(sid)}</td><td>{_source_state(cfg, st)}</td><td>{st["ok"]}/{st["richieste"] + st.get("saltate", 0)}</td>'
                        f'<td>{st["trovati"]}</td><td>{st["validi"]}</td><td>{_e(st["metodi"])}</td>'
                        f'<td class="model">{_e(st["ultimo_errore"])}</td></tr>')
    label = t(cfg, "report.partial", n=len(missing)) if missing else t(cfg, "report.total")
    total_tile = f'<div class="tile total"><div class="k">{_e(label)}</div><div class="v">{money(cfg, total)}</div></div>'
    when = f"{ts:%d/%m/%Y %H:%M}"
    n_checked = sum(bool((o.get("extra") or {}).get("ia")) for o in offers)
    checked_note = " " + t(cfg, "report.ai", n=n_checked) if n_checked else ""
    src_head = "".join(f"<th>{_e(h)}</th>" for h in t(cfg, "report.sources_head"))
    page = f"""<!doctype html><html lang="{lang(cfg)}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{t(cfg, "report.title")}</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>{t(cfg, "report.title")}</h1>
<p class="sub">{t(cfg, "report.updated", when=when)} · {t(cfg, "report.valid", n=len(offers))} · {t(cfg, "report.sorted")}</p>
<p class="sub">{t(cfg, "report.rel")}{checked_note}</p>
<div class="summary">{total_tile}{"".join(tiles)}</div>
{"".join(sections)}
<section class="comp"><div class="head"><h2>{t(cfg, "report.sources")}</h2></div><div class="scroll"><table class="src">
<thead><tr>{src_head}</tr></thead>
<tbody>{"".join(src_rows)}</tbody></table></div></section>
</div></body></html>"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return path
