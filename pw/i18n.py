"""Testi prodotti dal motore (avvisi, report, Telegram). I testi della GUI stanno in gui/app.js."""
from __future__ import annotations

TEXT = {
    "it": {
        "level.esatto": "Esatto", "level.superiore": "Superiore", "level.simile": "Simile", "level.incerto": "Incerto",
        "w.variants": "Inserzione con più varianti: il prezzo può essere quello di un'altra, verifica",
        "w.uncertain": "Somiglia solo in parte a ciò che cerchi ({score}%): verifica",
        "w.ai_kind": "Secondo l'IA locale è {kind}: verifica",
        "w.ai_value": "{name} {value}, letto dall'IA locale",
        "r.ai": "Secondo l'IA locale è {kind}", "r.ai_value": "{name} {value} fuori da {wanted}, letto dall'IA locale",
        "r.misread": "Prezzo troppo basso per essere vero: numero letto male",
        "ai.accessory": "un accessorio", "ai.whole_computer": "un computer intero", "ai.used": "un usato",
        "report.discarded": "Offerte scartate: {n}. Mostra le più vicine a ciò che cerchi", "report.discarded_head": ["Offerta", "Prezzo", "Sito", "Motivo"],
        "report.same_model": "Stesso modello: {n} offerte, da {price}", "report.ai": "L'IA locale ha controllato {n} offerte.",
        "w.similar_name": "Modello simile a quello cercato: {found} invece di {wanted}",
        "w.alt": "Alternativa indicata da te: {name}",
        "w.spec_missing": "{name} non indicata nel titolo: verifica",
        "w.spec_near": "{name}: {value} invece di {wanted}, dentro il margine",
        "w.spec_better": "{name}: {value}, meglio di {wanted}",
        "w.foreign": "Negozio estero: verifica spedizione nel tuo Paese",
        "w.converted": "Prezzo convertito da {orig} col cambio BCE del {date}: dogana e commissioni escluse",
        "w.telegram": "Segnalazione Telegram @{channel} {date}: verifica che sia ancora valida",
        "w.shop": "Negozio da verificare",
        "w.anomaly": "Prezzo anomalo: le offerte simili costano circa {price}, verifica cosa vende",
        "r.not_matching": "Non corrisponde al modello cercato",
        "r.excluded": "Contiene una parola esclusa: {word}",
        "r.spec_out": "{name}: {value} fuori dal margine ({wanted})",
        "r.system": "Computer intero, non il singolo prodotto ({word})",
        "r.price": "Nessun prezzo tra {lo} e {hi}",
        "rel.alta": "Affidabilità alta", "rel.media": "Affidabilità media", "rel.bassa": "Affidabilità bassa",
        "report.rel": "L'affidabilità dice quanto fidarsi di prezzo e prodotto. Scende per negozi esteri, prezzi convertiti, specifiche non indicate nel titolo, siti letti col browser o in modo approssimativo e segnalazioni Telegram. È bassa per prezzi anomali e negozi da verificare.",
        "report.browser": "browser non installato",
        "r.no_price": "Nessun prezzo leggibile",
        "report.title": "PriceWatch", "report.updated": "Aggiornato {when}", "report.valid": "{n} offerte valide",
        "report.sorted": "Prima i negozi senza dogana (il tuo Paese e l'UE), poi gli altri, ognuno dal prezzo più basso. Il prezzo in alto è l'offerta più affidabile, non per forza la più bassa.",
        "report.total": "Totale prodotti", "report.partial": "Parziale: mancano {n}",
        "report.none": "Nessuna offerta valida in questo giro.",
        "report.head": ["Totale", "Corrispondenza", "Offerta", "Negozio", "Note"],
        "report.more": "Mostra le altre {n} offerte", "report.pick": "Scelta più affidabile",
        "report.low": "Più basso ma da verificare: {price}", "report.delta": "{price} rispetto al minimo precedente",
        "report.sources": "Stato dei siti",
        "report.sources_head": ["Sito", "Stato", "Pagine lette", "Letti", "Validi", "Metodo", "Ultimo errore"],
        "report.ok": "ok", "report.blocked": "bloccato", "report.errors": "errori", "report.partial_src": "parziale",
        "report.zero": "0 risultati", "report.stopped": "fermato dopo errori ripetuti", "report.currency": "cambio non disponibile",
        "ship.free": "sped. inclusa", "ship.plus": "+ {price} sped.", "ship.na": "sped. n.d.",
        "tg.head": "📊 <b>Offerte più affidabili</b> · {when}", "tg.total": "Totale: <b>{price}</b>",
        "tg.partial": "Parziale, mancano {n}: <b>{price}</b>", "tg.none": "nessuna offerta valida",
        "tg.low": "<i>Più basso ma da verificare:</i>", "tg.file": "Elenco completo delle offerte: aprilo col browser",
        "tg.from": "da {orig}", "tg.threshold": "sotto la soglia di {price}", "tg.new_min": "nuovo minimo (prima {price})",
        "tg.test": "✅ PriceWatch: notifiche attive.",
    },
    "en": {
        "level.esatto": "Exact", "level.superiore": "Better", "level.simile": "Similar", "level.incerto": "Uncertain",
        "w.variants": "Listing with several variants: the price may be for another one, check it",
        "w.uncertain": "Only partly like what you want ({score}%): check it",
        "w.ai_kind": "The local AI thinks it is {kind}: check it",
        "w.ai_value": "{name} {value}, read by the local AI",
        "r.ai": "The local AI thinks it is {kind}", "r.ai_value": "{name} {value} outside {wanted}, read by the local AI",
        "r.misread": "Price too low to be true: a misread number",
        "ai.accessory": "an accessory", "ai.whole_computer": "a whole computer", "ai.used": "used",
        "report.discarded": "Discarded offers: {n}. Show the closest to what you want", "report.discarded_head": ["Offer", "Price", "Site", "Reason"],
        "report.same_model": "Same model: {n} offers, from {price}", "report.ai": "The local AI checked {n} offers.",
        "w.similar_name": "Similar model: {found} instead of {wanted}",
        "w.alt": "Alternative you listed: {name}",
        "w.spec_missing": "{name} not stated in the title: check it",
        "w.spec_near": "{name}: {value} instead of {wanted}, within your margin",
        "w.spec_better": "{name}: {value}, better than {wanted}",
        "w.foreign": "Foreign shop: check delivery to your country",
        "w.converted": "Price converted from {orig} at the ECB rate of {date}: customs and fees not included",
        "w.telegram": "Telegram post @{channel} {date}: check it is still valid",
        "w.shop": "Shop to check",
        "w.anomaly": "Unusual price: similar offers cost about {price}, check what is being sold",
        "r.not_matching": "Does not match the model you want",
        "r.excluded": "Contains an excluded word: {word}",
        "r.spec_out": "{name}: {value} outside your margin ({wanted})",
        "r.system": "Whole computer, not the single product ({word})",
        "r.price": "No price between {lo} and {hi}",
        "rel.alta": "High reliability", "rel.media": "Medium reliability", "rel.bassa": "Low reliability",
        "report.rel": "Reliability says how far to trust the price and the product. It drops for foreign shops, converted prices, specs missing from the title, sites read with the browser or approximately, and Telegram posts. It is low for unusual prices and shops to check.",
        "report.browser": "browser not installed",
        "r.no_price": "No readable price",
        "report.title": "PriceWatch", "report.updated": "Updated {when}", "report.valid": "{n} valid offers",
        "report.sorted": "Shops without customs first (your country and the EU), then the others, each from the lowest price. The price at the top is the most reliable offer, not always the lowest.",
        "report.total": "Products total", "report.partial": "Partial: {n} missing",
        "report.none": "No valid offers in this run.",
        "report.head": ["Total", "Match", "Offer", "Shop", "Notes"],
        "report.more": "Show {n} more offers", "report.pick": "Most reliable pick",
        "report.low": "Lower but to check: {price}", "report.delta": "{price} compared with the previous low",
        "report.sources": "Site status",
        "report.sources_head": ["Site", "Status", "Pages read", "Read", "Valid", "Method", "Last error"],
        "report.ok": "ok", "report.blocked": "blocked", "report.errors": "errors", "report.partial_src": "partial",
        "report.zero": "0 results", "report.stopped": "stopped after repeated errors", "report.currency": "no exchange rate",
        "ship.free": "free delivery", "ship.plus": "+ {price} delivery", "ship.na": "delivery n/a",
        "tg.head": "📊 <b>Most reliable offers</b> · {when}", "tg.total": "Total: <b>{price}</b>",
        "tg.partial": "Partial, {n} missing: <b>{price}</b>", "tg.none": "no valid offers",
        "tg.low": "<i>Lower but to check:</i>", "tg.file": "Full list of offers: open it in your browser",
        "tg.from": "from {orig}", "tg.threshold": "below your {price} threshold", "tg.new_min": "new low (was {price})",
        "tg.test": "✅ PriceWatch: notifications on.",
    },
}

SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF", "CAD": "C$", "AUD": "A$", "NZD": "NZ$", "SEK": "kr",
           "NOK": "kr", "DKK": "kr", "PLN": "zł", "CZK": "Kč", "JPY": "¥", "INR": "₹", "BRL": "R$", "MXN": "MX$",
           "SGD": "S$", "ZAR": "R", "TRY": "₺", "CNY": "CN¥", "HKD": "HK$", "KRW": "₩", "MYR": "RM", "THB": "฿", "PHP": "₱",
           "IDR": "Rp", "ILS": "₪", "RON": "lei", "HUF": "Ft"}
_SUFFIX = {"EUR", "SEK", "NOK", "DKK", "PLN", "CZK", "CHF", "RON", "HUF"}


def lang(cfg: dict) -> str:
    code = (cfg.get("generale") or {}).get("lingua", "it")
    return code if code in TEXT else "en"


def t(cfg: dict, key: str, **kw):
    value = TEXT[lang(cfg)].get(key, key)
    return value.format(**kw) if kw else value


def money(cfg: dict, v, currency: str | None = None) -> str:
    if v is None:
        return "—"
    cur = currency or (cfg.get("generale") or {}).get("valuta", "EUR")
    text = f"{v:,.2f}"
    if lang(cfg) == "it":
        text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    sym = SYMBOLS.get(cur, cur)
    return f"{text} {sym}" if cur in _SUFFIX else f"{sym}{text}"


def original_price(cfg: dict, offer: dict) -> str:
    """Il prezzo nella valuta del negozio, se l'offerta è stata convertita."""
    extra = offer.get("extra") or {}
    return money(cfg, extra["prezzo_orig"], extra["valuta_orig"]) if extra.get("valuta_orig") else ""
