"""Tests a site with a real search and says how many relevant offers it can read."""
from __future__ import annotations

from urllib.parse import quote_plus

from . import catalog, extract
from .fetch import Fetcher
from .rules import matches_phrase, norm


def test_site(site: dict, query: str = "samsung ssd", fetcher: Fetcher | None = None, home: str = "EUR") -> dict:
    cfg = {"generale": {"accept_language": catalog.ACCEPT_LANGUAGE.get(site.get("paese"))}}
    f = fetcher or Fetcher(cfg)
    url = site["url"].replace("{q}", quote_plus(query))
    try:
        page = f.get(url, browser=bool(site.get("browser")))
        cards = extract.card_links(page.html, page.url, site["espandi"], 3) if page.ok and site.get("espandi") else []
        for card in cards:  # comparison site with grouped results: the offers are inside the product page; one may fail to open
            page = f.get(card, browser=bool(site.get("browser")))
            if page.ok:
                break
    finally:
        if fetcher is None:
            f.close()
    if page.blocked:
        return {"esito": "bloccato", "dettaglio": f"HTTP {page.status}", "letti": 0, "pertinenti": 0}
    if not page.ok:
        return {"esito": "errore", "dettaglio": (page.error or f"HTTP {page.status}")[:120], "letti": 0, "pertinenti": 0}
    items, method = extract.listing_items(page.html, page.url, site.get("selettori"), site.get("negozio", ""), catalog.site_currency(site, home))
    # one word of the term is enough: comparison sites often shorten titles
    relevant = [i for i in items if any(matches_phrase(w, norm(i.title)) for w in query.split())]
    return {"esito": "ok" if relevant else "vuoto", "dettaglio": method, "letti": len(items), "pertinenti": len(relevant),
            "esempio": relevant[0].title[:90] if relevant else "", "prezzo": relevant[0].prices[0] if relevant else None}


def test_channel(handle: str, query: str, currency: str = "EUR") -> dict:
    f = Fetcher({})
    try:
        page = f.get(f"https://t.me/s/{handle}?q={quote_plus(query)}" if query else f"https://t.me/s/{handle}")
    finally:
        f.close()
    if not page.ok:
        return {"esito": "bloccato" if page.blocked else "errore", "dettaglio": page.error or f"HTTP {page.status}", "letti": 0}
    if "tgme_widget_message" not in page.html and "tgme_channel_info" not in page.html:
        return {"esito": "errore", "dettaglio": "not a public channel", "letti": 0}
    items, _ = extract.telegram_items(page.html, handle, 30, currency)
    return {"esito": "ok", "dettaglio": "telegram", "letti": len(items)}
