"""eBay offers from the official interface (Browse API). Needs a free key from developer.ebay.com."""
from __future__ import annotations

import time
from urllib.parse import quote_plus

import requests

from .extract import RawItem
from .fetch import Page

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
SCOPE = "https://api.ebay.com/oauth/api_scope"
MARKETPLACES = {"IT": "EBAY_IT", "DE": "EBAY_DE", "AT": "EBAY_AT", "FR": "EBAY_FR", "ES": "EBAY_ES", "NL": "EBAY_NL", "GB": "EBAY_GB", "CH": "EBAY_CH",
                "PL": "EBAY_PL", "US": "EBAY_US", "CA": "EBAY_ENCA", "AU": "EBAY_AU"}
_tokens: dict[str, tuple[str, float]] = {}


def enabled(cfg: dict) -> bool:
    keys = cfg.get("ebay") or {}
    return bool(keys.get("app_id") and keys.get("cert_id"))


def marketplace(country: str) -> str:
    return MARKETPLACES.get(country, "")


def search_url(query: str, market: str) -> str:
    return f"{SEARCH_URL}?q={quote_plus(query)}&market={market}"


def _token(cfg: dict, timeout: float = 20) -> str:
    keys = cfg["ebay"]
    saved = _tokens.get(keys["app_id"])
    if saved and saved[1] > time.time() + 60:
        return saved[0]
    r = requests.post(TOKEN_URL, auth=(keys["app_id"], keys["cert_id"]), timeout=timeout,
                      data={"grant_type": "client_credentials", "scope": SCOPE})
    r.raise_for_status()
    data = r.json()
    _tokens[keys["app_id"]] = (data["access_token"], time.time() + float(data.get("expires_in", 7200)))
    return data["access_token"]


def _item(raw: dict, market: str) -> RawItem | None:
    price = raw.get("price") or {}
    try:
        value = float(price["value"])
    except (KeyError, TypeError, ValueError):
        return None
    shipping = None
    for option in raw.get("shippingOptions") or []:
        cost = option.get("shippingCost") or {}
        if cost.get("value") is not None and cost.get("currency") == price.get("currency"):
            shipping = float(cost["value"])
            break
    seller = (raw.get("seller") or {}).get("username", "")
    return RawItem(raw.get("title", ""), [value], raw.get("itemWebUrl", ""), f"eBay {market.removeprefix('EBAY_')}", shipping, None, "ebay-api",
                   extra={"venditore": seller}, currency=str(price.get("currency", "")))


def search(cfg: dict, query: str, market: str, limit: int = 50, timeout: float = 25) -> tuple[Page, list[RawItem]]:
    """New fixed-price items only, cheapest first. Errors never contain keys or tokens."""
    url = search_url(query, market)
    try:
        r = requests.get(SEARCH_URL, timeout=timeout, headers={"Authorization": f"Bearer {_token(cfg)}", "X-EBAY-C-MARKETPLACE-ID": market},
                         params={"q": query, "limit": limit, "sort": "price", "filter": "conditions:{NEW},buyingOptions:{FIXED_PRICE}"})
        if r.status_code != 200:
            return Page(url, r.status_code, "", error=f"eBay API: HTTP {r.status_code}"), []
        items = [_item(x, market) for x in r.json().get("itemSummaries") or []]
        return Page(url, 200, "", via="ebay-api"), [i for i in items if i and i.title]
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else 0
        hint = "key rejected" if code in (400, 401) else f"HTTP {code}"
        return Page(url, code, "", error=f"eBay API: {hint}"), []
    except (requests.RequestException, ValueError, KeyError) as e:
        return Page(url, 0, "", error=f"eBay API: {type(e).__name__}"), []
