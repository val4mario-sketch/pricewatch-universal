"""Performs a complete run: downloads the sites, filters with the rules, saves, notifies."""
from __future__ import annotations

import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from html import escape
from statistics import median
from urllib.parse import quote_plus, urlparse

from . import ai, catalog, ebay, extract, notify, quality, rates
from .fetch import Fetcher, Page
from .i18n import money, original_price, t
from .rules import GENERIC_WORDS, Rules, model_code, norm, split_name

MAX_FAILURES = 2  # after two blocks or errors in a row, the site stops until the next run
MAX_CARDS = 5      # grouped product pages to open for each search on a comparison site
MISREAD_RATIO = 0.15  # below 15% of the median it is not an offer but a misread number (an instalment, a rating, 0.19)
MISREAD_MIN_OFFERS = 5


@dataclass
class Task:
    source: str
    kind: str              # ricerca | pagina | telegram
    url: str
    product: str
    query: str = ""
    sel: dict | None = None
    shop: str = ""
    browser: bool = False
    foreign: bool = False
    currency: str = "EUR"  # the one in which the site writes its prices
    handle: str = ""
    days: int = 7
    expand: str = ""
    customs: bool = False
    market: str = ""


@dataclass
class TaskResult:
    task: Task
    pages: list[Page] = field(default_factory=list)
    items: list[extract.RawItem] = field(default_factory=list)
    strategy: str = ""
    skipped: bool = False


def _without_generic(term: str) -> str:
    words = [w for w in term.split() if w.lower() not in GENERIC_WORDS]
    # "5070ti" is searched as shops write it; "9900X" is not: the single letter is part of the model
    return re.sub(r"\b(\d{3,})([a-zA-Z]{2})\b", r"\1 \2", " ".join(words) or term)


def search_terms(product: dict) -> list[str]:
    # a term equal to the name is the automatic one: "ram" or "kit" in the search only lose results
    terms = [_without_generic(q) if q == product.get("nome") else q for q in (product.get("ricerca") or [product.get("nome", "")])]
    return [q for q in dict.fromkeys(terms) if q.strip()]


def build_tasks(cfg: dict, only_product: str | None = None, table: dict | None = None) -> tuple[list[Task], dict[str, str]]:
    """Returns the requests to make and the skipped sites with the reason."""
    tasks, skipped = [], {}
    g = cfg.get("generale", {})
    home, currency = g.get("paese", "IT"), g.get("valuta", "EUR")
    sites = [s for s in catalog.site_list(cfg) if s["attivo"]]
    products = [p for p in cfg.get("prodotti", []) if p.get("attivo", True) and (not only_product or p["id"] == only_product)]
    usable = []
    for s in sites:
        if s.get("browser") and not Fetcher.browser_available():
            skipped[s["id"]] = "browser"
        elif rates.factor(table, catalog.site_currency(s, currency), currency) is None:
            skipped[s["id"]] = "currency"  # without a rate the prices could not be compared
        else:
            usable.append(s)
    for p in products:
        for q in search_terms(p):
            for s in usable:
                tasks.append(Task(s["id"], "ricerca", s["url"].replace("{q}", quote_plus(q)), p["id"], q, s.get("selettori"),
                                  s.get("negozio", ""), bool(s.get("browser")), s.get("paese") != home, catalog.site_currency(s, currency),
                                  expand=s.get("espandi") or "",
                                  customs=s.get("paese") != home and not (home in catalog.EU_COUNTRIES and s.get("paese") in catalog.EU_COUNTRIES)))
            for h in (cfg.get("telegram") or {}).get("canali") or []:
                tasks.append(Task("telegram", "telegram", f"https://t.me/s/{h}?q={quote_plus(q)}", p["id"], q, handle=h,
                                  currency=currency, days=int((cfg.get("telegram") or {}).get("giorni_max", 7))))
        terms = search_terms(p)
        for brand in catalog.brands_for(split_name(p.get("nome", ""))[0]) if terms else []:
            q = f"{brand} {terms[0]}"
            for s in usable:
                if s.get("marchi_cinesi"):
                    tasks.append(Task(s["id"], "ricerca", s["url"].replace("{q}", quote_plus(q)), p["id"], q, s.get("selettori"),
                                      s.get("negozio", ""), bool(s.get("browser")), s.get("paese") != home, catalog.site_currency(s, currency),
                                      customs=s.get("paese") != home and not (home in catalog.EU_COUNTRIES and s.get("paese") in catalog.EU_COUNTRIES)))
        market = ebay.marketplace(home) if ebay.enabled(cfg) else ""
        for q in search_terms(p) if market else []:
            tasks.append(Task("ebay_api", "ebay", ebay.search_url(q, market), p["id"], q, shop=f"eBay {home}", currency=currency, market=market))
        for u in p.get("pagine") or []:
            tasks.append(Task("pagine", "pagina", u, p["id"], currency=currency))
    return tasks, skipped


def run_task(f: Fetcher, t_: Task, cfg: dict | None = None) -> TaskResult:
    res = TaskResult(t_)
    if t_.kind == "ebay":
        page, res.items = ebay.search(cfg or {}, t_.query, t_.market)
        res.pages.append(page)
        res.strategy = "ebay-api"
        return res
    p = f.get(t_.url, browser=t_.browser)
    res.pages.append(p)
    if not p.ok:
        return res
    if t_.kind == "telegram":
        res.items, _ = extract.telegram_items(p.html, t_.handle, t_.days, t_.currency)
        res.strategy = "telegram"
    elif t_.kind == "pagina":
        res.items, res.strategy = extract.product_page_item(p.html, p.url, cur=t_.currency)
    else:
        cards = extract.card_links(p.html, p.url, t_.expand, MAX_CARDS) if t_.expand else []
        if not cards:
            res.items, res.strategy = extract.listing_items(p.html, p.url, t_.sel, t_.shop, t_.currency)
        for url in cards:  # the product page price is a "from...": the real offers, with the shop, are inside
            q = f.get(url, browser=t_.browser)
            res.pages.append(q)
            if q.ok:
                items, res.strategy = extract.listing_items(q.html, q.url, t_.sel, t_.shop, t_.currency)
                res.items += items
    return res


def execute(cfg: dict, tasks: list[Task], log=print) -> list[TaskResult]:
    f = Fetcher(cfg)
    by_host: dict[str, list[Task]] = defaultdict(list)
    browser_hosts: dict[str, list[Task]] = defaultdict(list)
    for t_ in tasks:
        (browser_hosts if t_.browser else by_host)[urlparse(t_.url).netloc].append(t_)
    results: list[TaskResult] = []

    def worker(host_tasks: list[Task]) -> list[TaskResult]:
        out, failures = [], 0
        for t_ in host_tasks:
            if failures >= MAX_FAILURES:
                out.append(TaskResult(t_, skipped=True))
                continue
            r = run_task(f, t_, cfg)
            p = next((x for x in r.pages if x.ok), r.pages[-1])  # one page read is enough: the site responds
            failures = 0 if p.ok else failures + 1
            state = "ok" if p.ok else ("BLOCKED" if p.blocked else f"error {p.status} {p.error}")
            log(f"  [{t_.source:16}] {(t_.query or t_.handle or t_.url[:40])[:32]:32} -> {state[:70]:10} {len(r.items):3}")
            out.append(r)
        return out

    try:
        if by_host:
            with ThreadPoolExecutor(max_workers=min(8, len(by_host))) as ex:
                for chunk in ex.map(worker, by_host.values()):
                    results += chunk
        for host_tasks in browser_hosts.values():  # Playwright is not thread-safe: queued, but a blocked site does not stop the others
            results += worker(host_tasks)
    finally:
        f.close()
    return results


def classify_results(cfg: dict, rules: Rules, results: list[TaskResult], table: dict | None = None,
                     rejected: list[dict] | None = None) -> tuple[list[dict], dict]:
    rejected = [] if rejected is None else rejected
    offers, seen = [], set()
    home = cfg.get("generale", {}).get("valuta", "EUR")
    stats: dict[str, dict] = defaultdict(lambda: {"richieste": 0, "ok": 0, "bloccate": 0, "errori": 0, "saltate": 0,
                                                  "trovati": 0, "validi": 0, "metodi": set(), "ultimo_errore": ""})
    for r in results:
        st = stats[r.task.source]
        st["saltate"] += r.skipped
        for p in r.pages:
            st["richieste"] += 1
            if p.ok:
                st["ok"] += 1
            elif p.blocked:
                st["bloccate"] += 1
                st["ultimo_errore"] = f"HTTP {p.status} / anti-bot"
            else:
                st["errori"] += 1
                st["ultimo_errore"] = p.error or f"HTTP {p.status}"
        if r.strategy:
            st["metodi"].add(r.strategy)
        st["trovati"] += len(r.items)
        for it in r.items:
            source_currency = it.currency or r.task.currency
            k = rates.factor(table, source_currency, home)
            if k is None:
                continue  # price in a currency with no rate: cannot be compared
            # minimum, maximum and threshold are in your currency: convert before judging
            d = rules.classify(it.title, [p * k for p in it.prices], None if it.shipping is None else it.shipping * k,
                               None if it.total is None else it.total * k, r.task.product)
            if not d.ok:
                rejected.append({"component": r.task.product, "title": it.title[:200], "price": round(min(it.prices) * k, 2) if it.prices else None,
                                 "source": r.task.source, "reason": d.reason, "score": d.score})
                continue
            title = re.sub(r"^(?:annuncio sponsorizzato|sponsored ad)\s*[–-]\s*", "", it.title, flags=re.I)
            shop = it.shop or r.task.shop or extract.shop_from_url(it.url)
            warns = list(d.warnings)
            if r.task.foreign:
                warns.append(t(cfg, "w.foreign"))
            if r.task.kind == "telegram":
                warns.append(t(cfg, "w.telegram", channel=it.extra.get("canale"), date=it.extra.get("data", "")[:10]))
            extra = {**it.extra, "metodo": r.strategy, "estero": r.task.foreign, "dogana": r.task.customs, "browser": r.task.browser, "spec_non_lette": d.unread,
                     "codice": model_code(title), "punteggio": d.score, "varianti": d.variants}
            if source_currency != home:
                extra = {**extra, "valuta_orig": source_currency, "prezzo_orig": round(d.price / k, 2)}
                warns.append(t(cfg, "w.converted", orig=money(cfg, extra["prezzo_orig"], source_currency),
                               date=f"{datetime.fromisoformat(table['data']):%d/%m/%Y}"))
            key = (d.component, norm(title)[:70], shop.lower(), d.price)
            if key in seen:
                continue
            seen.add(key)
            st["validi"] += 1
            offers.append({"component": d.component, "model": d.model, "level": d.level, "title": title,
                           "price": round(d.price, 2), "shipping": None if d.shipping is None else round(d.shipping, 2),
                           "total": d.total, "shop": shop, "source": r.task.source, "url": it.url, "warnings": warns,
                           "tags": d.tags, "extra": extra})
    for st in stats.values():
        st["metodi"] = ", ".join(sorted(st["metodi"]))
    # same link found by several searches: keep the lowest price
    best_by_url: dict[tuple, dict] = {}
    for o in offers:
        k = (o["component"], o["url"].split("#")[0])
        if k not in best_by_url or o["total"] < best_by_url[k]["total"]:
            best_by_url[k] = o
    ordered = sorted(best_by_url.values(), key=lambda o: (o["component"], o["total"]))
    kept = drop_misread(ordered)
    rejected += [{"component": o["component"], "title": o["title"][:200], "price": o["total"], "source": o["source"], "reason": t(cfg, "r.misread"),
                  "score": (o.get("extra") or {}).get("punteggio", 0)} for o in ordered if o not in kept]
    return kept, dict(stats)


def drop_misread(offers: list[dict]) -> list[dict]:
    totals = defaultdict(list)
    for o in offers:
        totals[o["component"]].append(o["total"])
    return [o for o in offers if len(totals[o["component"]]) < MISREAD_MIN_OFFERS
            or o["total"] >= MISREAD_RATIO * median(totals[o["component"]])]


def alerts(cfg: dict, rules: Rules, store, run_id: int, offers: list[dict], log=print) -> list[str]:
    ncfg = cfg.get("notifiche", {}) or {}
    margin = float(ncfg.get("margine_minimo_pct", 1)) / 100
    msgs = []
    for cid, comp in rules.components.items():
        offs = [o for o in offers if o["component"] == cid]
        if not offs:
            continue
        best = quality.pick(offs)
        prev = store.min_before(cid, run_id)
        why = []
        soglia = comp.get("soglia_avviso")
        if soglia not in (None, "") and best["total"] <= float(soglia):
            why.append(t(cfg, "tg.threshold", price=money(cfg, float(soglia))))
        if ncfg.get("nuovo_minimo", True) and prev is not None and best["total"] < prev * (1 - margin):
            why.append(t(cfg, "tg.new_min", price=money(cfg, prev)))
        # for a converted offer the shop's price is what counts: if only the rate moves, the alert is not repeated
        key = f"{cid}|{best['url']}|{round((best.get('extra') or {}).get('prezzo_orig') or best['total'])}"
        # Alert not delivered in a previous run: the offer is now part of the
        # history and would no longer be a "new low", so the saved reason is reused.
        if not why and store.pending_why(key):
            why.append(store.pending_why(key))
        if not why or store.was_notified(key):
            continue
        # Telegram refuses the message if & or < in the text are not encoded
        label = t(cfg, f"level.{best.get('level')}")
        orig = original_price(cfg, best)
        origin = f" ({t(cfg, 'tg.from', orig=escape(orig))})" if orig else ""
        txt = (f"💸 <b>{escape(rules.name(cid))}</b>: {money(cfg, best['total'])}{origin} — {escape(', '.join(why))}\n"
               f"{escape(label)} · {escape(t(cfg, 'rel.' + quality.grade(best)))} · {escape(best['shop'])} ({escape(best['source'])})\n"
               f"{escape(best['title'][:150])}\n{escape(best['url'])}")
        msgs.append(txt)
        res = notify.send(cfg, txt)
        log(f"  notification {cid}: {res}")
        if res == "ok":
            store.mark_notified(key)
        else:
            store.mark_pending(key, ", ".join(why))
    return msgs


def run(cfg: dict, store, log=print, only_product=None) -> int:
    rules = Rules(cfg)
    table = rates.get(log)
    tasks, skipped = build_tasks(cfg, only_product, table)
    log(f"{datetime.now():%H:%M:%S}  {len(tasks)} requests…")
    results = execute(cfg, tasks, log)
    rejected: list[dict] = []
    offers, stats = classify_results(cfg, rules, results, table, rejected)
    offers = ai.review(cfg, rules, offers, store, rejected, log)
    for sid, why in skipped.items():
        stats[sid] = {"richieste": 0, "ok": 0, "bloccate": 0, "errori": 0, "saltate": 0, "trovati": 0, "validi": 0,
                      "metodi": "", "ultimo_errore": "", "stato": why}
    run_id = store.new_run()
    best = quality.picks(offers, cfg)
    msgs = alerts(cfg, rules, store, run_id, offers, log)
    for o in offers:
        o.pop("dubbia", None)
        o.pop("stesso_modello", None)
    store.add_offers(run_id, offers)
    store.add_discarded(run_id, rejected)
    store.add_best(run_id, {c: o["total"] for c, o in best.items()})
    store.finish_run(run_id, stats)
    store.prune()
    log(f"{datetime.now():%H:%M:%S}  {len(offers)} valid offers, {len(msgs)} alerts.")
    return run_id
