"""Extraction of offers (title, prices, link, shop) from HTML pages.

Strategies, in order:
  1. CSS selectors configured for the source
  2. JSON-LD structured data (schema.org Product / ItemList)
  3. heuristic extractor: each price in the site's currency is paired with the nearest
     product link in the DOM. It is noisy, but the component rules discard
     anything that does not match, so the noise does not reach the report.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

# ------------------------------------------------------------------ prices
_NUM = r"(?<![\w.,])(?:\d{1,3}(?:[.  ]\d{3})+(?:,\d{1,2})?|\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:[.,]\d{1,2})?)"
_SPLIT_EURO = re.compile(r"(?<![\d.,])(\d{1,4})\s*€\s*(\d{2})(?!\d)")  # "457€95" (LDLC)

# How each currency appears next to the price. A plain dollar sign is used by several countries: the site's currency decides.
CURRENCY_TOKENS = {
    "EUR": r"€|\beur\b|\beuro\b",
    "USD": r"us\$|\$|\busd\b",
    "GBP": r"£|\bgbp\b",
    "CHF": r"\bchf\b",
    "CAD": r"c\$|ca\$|\$|\bcad\b",
    "AUD": r"a\$|au\$|\$|\baud\b",
    "NZD": r"nz\$|\$|\bnzd\b",
    "SEK": r"\bkr\b|\bsek\b|:-",
    "NOK": r"\bkr\b|\bnok\b|,-",
    "DKK": r"\bkr\b|\bdkk\b",
    "PLN": r"zł|\bpln\b",
    "CZK": r"kč|\bczk\b",
    "JPY": r"¥|円|\bjpy\b",
    "INR": r"₹|\brs\.?(?=\s*\d)|\binr\b",
    "BRL": r"r\$|\bbrl\b",
    "MXN": r"mx\$|\$|\bmxn\b",
    "SGD": r"s\$|\$|\bsgd\b",
    "ZAR": r"\br(?=\s*\d)|\bzar\b",
    "TRY": r"₺|\btl\b|\btry\b",
    "CNY": r"¥|￥|元|\brmb\b|\bcny\b",
    "HKD": r"hk\$|\$|\bhkd\b",
    "KRW": r"₩|원|\bkrw\b",
    "MYR": r"\brm(?=\s*\d)|\bmyr\b",
    "THB": r"฿|บาท|\bthb\b|\.-",
    "PHP": r"₱|\bphp\b",
    "IDR": r"\brp\.?(?=\s*\d)|\bidr\b",
    "ILS": r"₪|\bils\b",
    "RON": r"\blei\b|\bron\b",
    "HUF": r"\bft\b|\bhuf\b",
}
_RX_CACHE: dict[str, tuple] = {}
_SPACE_THOUSANDS = {"PLN", "SEK", "NOK", "DKK", "CZK", "HUF"}  # "4 299 zł"; elsewhere "2 399" can be a quantity and a price


def _money_rx(cur: str) -> tuple:
    if cur not in _RX_CACHE:
        tok = CURRENCY_TOKENS.get(cur, CURRENCY_TOKENS["EUR"])
        _RX_CACHE[cur] = (re.compile(r"(" + _NUM + r")\s*(?:" + tok + r")", re.I),
                          re.compile(r"(?:" + tok + r")\s*(" + _NUM + r")", re.I),
                          re.compile(tok, re.I))
    return _RX_CACHE[cur]


def to_float(s: str) -> float | None:
    s = s.replace(" ", "").replace(" ", "").replace(" ", "").strip()
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        s = s.replace(",", ".") if len(parts) == 2 and len(parts[1]) in (1, 2) else s.replace(",", "")
    elif "." in s:
        parts = s.split(".")
        if len(parts) > 2 or len(parts[-1]) == 3:
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def prices_in(text: str, cur: str = "EUR") -> list[tuple[float, int, int]]:
    """All the prices in the given currency found in the text: (value, start, end)."""
    if not text:
        return []
    found: list[tuple[float, int, int]] = []
    if cur in _SPACE_THOUSANDS:  # same length: positions stay valid
        text = re.sub(r"(?<=\d) (?=\d{3}(?!\d))", " ", text)
    work = text
    for m in (_SPLIT_EURO.finditer(text) if cur == "EUR" else ()):
        v = to_float(f"{m.group(1)},{m.group(2)}")
        if v is not None:
            found.append((v, m.start(), m.end()))
        work = work[: m.start()] + " " * (m.end() - m.start()) + work[m.end():]
    taken: list[tuple[int, int]] = []
    for rx in _money_rx(cur)[:2]:
        for m in rx.finditer(work):
            if any(not (m.end() <= a or m.start() >= b) for a, b in taken):
                continue
            v = to_float(m.group(1))
            if v is not None and v > 0:
                found.append((v, m.start(), m.end()))
                taken.append((m.start(), m.end()))
    found.sort(key=lambda x: x[1])
    return found


_SHIP_FREE = re.compile(r"sped(?:izione|\.)?\s*(?:gratuita|gratis|inclusa)|free (?:shipping|delivery)|kostenloser versand|versandkostenfrei"
                        r"|livraison gratuite|env[ií]o gratis|gratis verzending|darmowa dostawa", re.I)
_SHIP_KW = re.compile(r"sped(?:izione|\.)?|shipping|delivery|versand|consegna|livraison|env[ií]o|verzending|dostawa", re.I)
_TOT_KW = re.compile(r"\b(?:tot(?:ale|\.)?|total|gesamt)\b", re.I)


def shipping_and_total(text: str, cur: str = "EUR") -> tuple[float | None, float | None]:
    ship = 0.0 if _SHIP_FREE.search(text or "") else None
    total = None
    plist = prices_in(text or "", cur)
    for kw, kind in ((_SHIP_KW, "s"), (_TOT_KW, "t")):
        for m in kw.finditer(text or ""):
            for v, a, _b in plist:
                if 0 <= a - m.end() <= 25:
                    if kind == "s" and ship is None:
                        ship = v
                    elif kind == "t" and total is None:
                        total = v
                    break
    return ship, total


# ------------------------------------------------------------------ modello
@dataclass
class RawItem:
    title: str
    prices: list[float]
    url: str = ""
    shop: str = ""
    shipping: float | None = None
    total: float | None = None
    strategy: str = ""
    extra: dict = field(default_factory=dict)
    currency: str = ""  # currency declared by the page; empty = the site's currency


def _clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _text_of(el: Tag | None) -> str:
    if el is None:
        return ""
    for attr in ("aria-label", "title", "alt"):
        v = el.get(attr) if hasattr(el, "get") else None
        if v and len(v) > 10:
            return _clean(v)
    return _clean(el.get_text(" ", strip=True))


def shop_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    aliases = {"amzn.to": "Amazon", "amzn.eu": "Amazon", "s.click.aliexpress.com": "AliExpress",
               "ebay.us": "eBay", "ebay.to": "eBay"}
    return aliases.get(host, host)


# ------------------------------------------------------------------ 1. selettori
def selector_items(soup: BeautifulSoup, sel: dict, base_url: str, fixed_shop: str = "", cur: str = "EUR") -> list[RawItem]:
    out: list[RawItem] = []
    item_sel = sel.get("item")
    if not item_sel:
        return out
    for card in soup.select(item_sel):
        tel = card.select_one(sel["titolo"]) if sel.get("titolo") else None
        title = _text_of(tel)
        if len(title) < 8:
            continue
        pel = card.select_one(sel["prezzo"]) if sel.get("prezzo") else None
        prices = [p[0] for p in prices_in(pel.get_text(" ", strip=True) if pel else "", cur)]
        card_text = card.get_text(" ", strip=True)
        if not prices:
            prices = [p[0] for p in prices_in(card_text, cur)]
        if not prices:
            continue
        link = None
        if sel.get("link"):
            link = card.select_one(sel["link"])
        if link is None and tel is not None:
            link = tel if tel.name == "a" else tel.find("a", href=True) or tel.find_parent("a", href=True)
        if link is None:
            link = card if card.name == "a" and card.get("href") else card.find("a", href=True)
        url = urljoin(base_url, link["href"]) if link is not None and link.get("href") else base_url
        ship = None
        if sel.get("spedizione"):
            sel_ship = card.select_one(sel["spedizione"])
            if sel_ship is not None:
                st = sel_ship.get_text(" ", strip=True)
                ship = 0.0 if _SHIP_FREE.search(st) or "gratis" in st.lower() else next(iter(p[0] for p in prices_in(st, cur)), None)
        s2, total = shipping_and_total(card_text, cur)
        shop = fixed_shop
        if not shop and sel.get("negozio"):
            sh = card.select_one(sel["negozio"])
            shop = _text_of(sh) if sh is not None else ""
        out.append(RawItem(title, prices, url, shop, ship if ship is not None else s2, total, "selettori"))
    return out


# ------------------------------------------------------------------ 2. JSON-LD
def _iter_jsonld(soup: BeautifulSoup):
    for sc in soup.find_all("script", type=lambda t: t and "ld+json" in t):
        raw = sc.string or sc.get_text() or ""
        try:
            data = json.loads(raw)
        except Exception:
            try:
                data = json.loads(re.sub(r",\s*([}\]])", r"\1", raw))
            except Exception:
                continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                yield d
                for k in ("@graph", "itemListElement", "item", "mainEntity"):
                    if k in d:
                        stack.append(d[k])


def _types(d: dict) -> set[str]:
    t = d.get("@type", "")
    return {x.lower() for x in (t if isinstance(t, list) else [t]) if isinstance(x, str)}


def _currency_code(value) -> str:
    code = str(value or "").strip().upper()
    return code if re.fullmatch(r"[A-Z]{3}", code) else ""


def _offer_prices(offers) -> tuple[list[float], str, str, str]:
    prices, url, seller, currency = [], "", "", ""
    for o in offers if isinstance(offers, list) else [offers]:
        if not isinstance(o, dict):
            continue
        spec = o.get("priceSpecification") if isinstance(o.get("priceSpecification"), dict) else {}
        code = _currency_code(o.get("priceCurrency") or spec.get("priceCurrency"))
        if code and currency and code != currency:
            continue  # the same offer in several currencies: the prices must not be mixed
        currency = currency or code
        for k in ("price", "lowPrice"):
            v = o.get(k)
            if v is None and isinstance(o.get("priceSpecification"), dict):
                v = o["priceSpecification"].get("price")
            if v is not None:
                f = to_float(str(v)) if not isinstance(v, (int, float)) else float(v)
                if f:
                    prices.append(f)
        url = url or o.get("url", "")
        s = o.get("seller")
        if isinstance(s, dict):
            seller = seller or s.get("name", "")
    return prices, url, seller, currency


def jsonld_products(soup: BeautifulSoup, base_url: str, only_lists: bool = False) -> list[RawItem]:
    out: list[RawItem] = []
    seen = set()
    for d in _iter_jsonld(soup):
        if "product" not in _types(d):
            continue
        name = _clean(d.get("name"))
        if not name:
            continue
        offers = d.get("offers")
        if offers is None:
            continue
        if only_lists and isinstance(offers, dict) and "aggregateoffer" in _types(offers):
            continue  # aggregate price for a product family: not reliable
        prices, url, seller, currency = _offer_prices(offers)
        if not prices:
            continue
        key = (name, tuple(prices))
        if key in seen:
            continue
        seen.add(key)
        out.append(RawItem(name, prices, urljoin(base_url, url or d.get("url", "") or base_url),
                           seller, None, None, "json-ld", currency=currency))
    if only_lists and len(out) < 2:
        return []
    return out


# ------------------------------------------------------------------ meta tag
def meta_product(soup: BeautifulSoup, base_url: str) -> RawItem | None:
    def meta(*names):
        for n in names:
            m = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n}) \
                or soup.find("meta", attrs={"itemprop": n})
            if m and m.get("content"):
                return m["content"]
        return None
    price = meta("product:price:amount", "og:price:amount", "price")
    if price is None:
        ip = soup.find(attrs={"itemprop": "price"})
        if ip is not None:
            price = ip.get("content") or ip.get_text(" ", strip=True)
    if price is None:
        return None
    f = to_float(str(price))
    if not f:
        return None
    h1 = soup.find("h1")
    title = _clean(meta("og:title") or (h1.get_text(" ", strip=True) if h1 else "") or (soup.title.string if soup.title else ""))
    return RawItem(title, [f], base_url, "", None, None, "meta",
                   currency=_currency_code(meta("product:price:currency", "og:price:currency", "priceCurrency")))


# ------------------------------------------------------------------ 3. euristica
_PRODUCTISH = re.compile(r"[a-zA-Z]{2,}.*\d|\d.*[a-zA-Z]{2,}")


def _good_anchors(node: Tag, cur: str = "EUR") -> list[Tag]:
    res = []
    for a in node.find_all("a", href=True):
        t = _text_of(a)
        if len(t) >= 15 and _PRODUCTISH.search(t) and not prices_in(t[:40], cur):
            res.append(a)
    return res


def heuristic_items(soup: BeautifulSoup, base_url: str, fixed_shop: str = "", cur: str = "EUR") -> list[RawItem]:
    out: list[RawItem] = []
    seen_cards: set[int] = set()
    seen_keys: set = set()
    for s in soup.find_all(string=_money_rx(cur)[2]):
        node = s.parent
        if node is None or node.name in ("script", "style", "noscript", "title", "option"):
            continue
        card = None
        for _ in range(9):
            if node is None or node.name in ("body", "html", "[document]"):
                break
            if len(node.get_text(" ", strip=True)) > 3000:
                break
            anchors = _good_anchors(node, cur)
            if anchors:
                distinct = {_text_of(a)[:60] for a in anchors}
                if len(distinct) <= 3:
                    card = node
                break
            node = node.parent
        if card is None or id(card) in seen_cards:
            continue
        seen_cards.add(id(card))
        anchors = sorted(_good_anchors(card, cur), key=lambda a: len(_text_of(a)), reverse=True)
        a = anchors[0]
        title = _text_of(a)
        text = card.get_text(" ", strip=True)
        prices = [p[0] for p in prices_in(text, cur)]
        if not prices:
            continue
        url = urljoin(base_url, a["href"])
        key = (title, url)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        shop = fixed_shop
        if not shop:
            sh = card.find(class_=re.compile(r"merchant|shop|seller|store|negozio|venditore|vendor", re.I))
            if sh is not None:
                img = sh.find("img", alt=True)
                shop = _clean(img["alt"]) if img is not None else _clean(sh.get_text(" ", strip=True))[:40]
        ship, total = shipping_and_total(text, cur)
        out.append(RawItem(title, prices, url, shop, ship, total, "euristica"))
    return out


def card_links(html: str, base_url: str, css: str, limit: int) -> list[str]:
    """The links of a comparison site's grouped product pages."""
    found = [urljoin(base_url, a["href"]) for a in BeautifulSoup(html, "lxml").select(css) if a.get("href")]
    return list(dict.fromkeys(found))[:limit]


def listing_items(html: str, base_url: str, sel: dict | None, fixed_shop: str = "", cur: str = "EUR") -> tuple[list[RawItem], str]:
    soup = BeautifulSoup(html, "lxml")
    if sel:
        items = selector_items(soup, sel, base_url, fixed_shop, cur)
        if items:
            return items, "selettori"
    items = jsonld_products(soup, base_url, only_lists=True)
    heur = heuristic_items(soup, base_url, fixed_shop, cur)
    if items:
        return items + heur, "json-ld+euristica"
    return heur, "euristica"


def product_page_item(html: str, base_url: str, sel: dict | None = None, cur: str = "EUR") -> tuple[list[RawItem], str]:
    soup = BeautifulSoup(html, "lxml")
    items = jsonld_products(soup, base_url)
    if items:
        for it in items:
            it.url = base_url
            it.shop = it.shop or shop_from_url(base_url)
        return items[:1], "json-ld"
    m = meta_product(soup, base_url)
    if m:
        m.shop = shop_from_url(base_url)
        return [m], "meta"
    # Amazon and similar
    t = soup.select_one("#productTitle")
    p = soup.select_one("#corePrice_feature_div .a-offscreen, #corePriceDisplay_desktop_feature_div .a-offscreen, .a-price .a-offscreen")
    if t is not None and p is not None:
        pr = [x[0] for x in prices_in(p.get_text(), cur)]
        if pr:
            return [RawItem(_clean(t.get_text()), pr, base_url, shop_from_url(base_url), None, None, "amazon")], "amazon"
    h1 = soup.find("h1")
    if h1 is not None:
        node = h1
        for _ in range(6):
            node = node.parent
            if node is None:
                break
            pr = [x[0] for x in prices_in(node.get_text(" ", strip=True), cur)]
            if pr:
                return [RawItem(_clean(h1.get_text(" ", strip=True)), pr, base_url, shop_from_url(base_url), None, None, "euristica")], "euristica"
    return [], "nessuna"


# ------------------------------------------------------------------ Telegram
def telegram_items(html: str, handle: str, max_days: int, cur: str = "EUR") -> tuple[list[RawItem], int | None]:
    """Reads the public page t.me/s/<channel>. Returns (offers, oldest_id)."""
    soup = BeautifulSoup(html, "lxml")
    out: list[RawItem] = []
    oldest = None
    limit = datetime.now(timezone.utc) - timedelta(days=max_days)
    for w in soup.select("div.tgme_widget_message"):
        post = w.get("data-post", "")
        try:
            pid = int(post.rsplit("/", 1)[1])
            oldest = pid if oldest is None else min(oldest, pid)
        except (IndexError, ValueError):
            pid = None
        tel = w.select_one(".tgme_widget_message_text")
        if tel is None:
            continue
        tm = w.select_one(".tgme_widget_message_date time")
        when = None
        if tm is not None and tm.get("datetime"):
            try:
                when = datetime.fromisoformat(tm["datetime"].replace("Z", "+00:00"))
            except ValueError:
                when = None
        if when is not None and when < limit:
            continue
        text = tel.get_text("\n", strip=True)
        prices = [p[0] for p in prices_in(text, cur)]
        if not prices:
            continue
        links = [a["href"] for a in tel.select("a[href]")
                 if not urlparse(a["href"]).netloc.endswith(("t.me", "telegram.me"))]
        url = links[0] if links else f"https://t.me/{post}"
        title = _clean(text.replace("\n", " "))[:300]
        out.append(RawItem(title, prices, url, shop_from_url(url) if links else "Telegram", None, None, "telegram",
                           {"canale": handle, "post": f"https://t.me/{post}", "data": when.isoformat() if when else ""}))
    return out, oldest
