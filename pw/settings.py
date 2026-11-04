"""Configurazione scritta dalla GUI: lettura, valori iniziali e controlli prima di salvare."""
from __future__ import annotations

import locale
import os
import re
import uuid
from pathlib import Path

import yaml

from . import catalog

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("PW_DATA") or ROOT / "dati")
CONFIG = DATA / "config.yaml"
OPS = {"min", "max", "eq", "text"}
LEVELS = {"simile", "superiore"}


def _guess_country() -> str:
    code = (locale.getlocale()[0] or "").replace("-", "_")
    known = re.search(r"_([A-Z]{2})\b", code)
    names = {"Italian": "IT", "German": "DE", "French": "FR", "Spanish": "ES", "English_United Kingdom": "GB", "English_United States": "US"}
    guess = known.group(1) if known else next((v for k, v in names.items() if code.startswith(k)), "US")
    return guess if guess in catalog.COUNTRIES else "US"


def defaults() -> dict:
    country = _guess_country()
    return {
        "generale": {"lingua": "en", "paese": country, "valuta": catalog.CURRENCY_OF.get(country, "EUR"),
                     "accept_language": catalog.ACCEPT_LANGUAGE.get(country), "intervallo_ore": 3, "apri_report": True,
                     "negozi_da_verificare": ["aliexpress"], "offerte_per_prodotto": 8,
                     "pausa_min_sec": 3, "pausa_max_sec": 6, "timeout_sec": 25, "impersona_browser": True,
                     "ia_attiva": True, "ia_modello": "", "ia_max_offerte": 40, "ia_max_sec": 300},
        "prodotti": [],
        "siti": {"attivi": catalog.default_active(), "visti": [s["id"] for s in catalog.SITES], "rimossi": [], "personalizzati": [], "esiti": {}},
        "telegram": {"canali": [], "giorni_max": 7},
        "ebay": {"app_id": "", "cert_id": ""},
        "notifiche": {"telegram_token": "", "telegram_chat_id": "", "nuovo_minimo": True, "margine_minimo_pct": 1, "riepilogo": True},
    }


def load() -> dict:
    cfg = defaults()
    if CONFIG.exists():
        saved = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
        for key, value in saved.items():
            cfg[key] = {**cfg[key], **value} if isinstance(cfg.get(key), dict) and isinstance(value, dict) else value
        # Un sito funzionante aggiunto al catalogo dopo l'ultimo salvataggio si accende; uno che l'utente ha spento resta spento.
        sites = saved.get("siti") or {}
        seen = sites.get("visti") or sites.get("attivi") or []
        removed = cfg["siti"].get("rimossi") or []
        cfg["siti"]["attivi"] = [*cfg["siti"]["attivi"], *(x for x in catalog.newly_working(seen) if x not in removed and x not in cfg["siti"]["attivi"])]
        cfg["siti"]["visti"] = [s["id"] for s in catalog.SITES]
    return cfg


def save(cfg: dict) -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    os.replace(tmp, CONFIG)  # niente file a metà se il PC si spegne mentre salva
    return cfg


def _number(value, label: str) -> float | None:
    if value in (None, ""):
        return None
    try:
        n = float(str(value).replace(",", "."))
    except ValueError:
        raise ValueError(f"{label}: {value}") from None
    if n < 0:
        raise ValueError(f"{label}: {value}")
    return n


def _words(values) -> list[str]:
    return [str(v).strip() for v in values or [] if str(v).strip()]


def clean_product(p: dict) -> dict:
    name = str(p.get("nome") or "").strip()
    if not name:
        raise ValueError("name")
    lo, hi = _number(p.get("prezzo_min"), "min"), _number(p.get("prezzo_max"), "max")
    if lo is not None and hi is not None and lo > hi:
        raise ValueError("min>max")
    specs = []
    for s in p.get("specifiche") or []:
        value = str(s.get("valore") or "").strip()
        if not value:
            continue
        op = s.get("op") if s.get("op") in OPS else "min"
        if op != "text":
            _number(value, str(s.get("nome") or "spec"))
        specs.append({"nome": str(s.get("nome") or "").strip(), "op": op, "valore": value,
                      "unita": str(s.get("unita") or "").strip(), "margine_pct": _number(s.get("margine_pct"), "margin") or 0})
    alternatives = [{"testo": str(a.get("testo")).strip(), "tipo": a.get("tipo") if a.get("tipo") in LEVELS else "simile"}
                    for a in p.get("alternative") or [] if str(a.get("testo") or "").strip()]
    pages = _words(p.get("pagine"))
    for u in pages:
        if not re.match(r"https?://", u):
            raise ValueError(f"url: {u}")
    return {"id": p.get("id") or uuid.uuid4().hex[:8], "nome": name, "attivo": bool(p.get("attivo", True)),
            "ricerca": _words(p.get("ricerca")) or [name], "specifiche": specs, "prezzo_min": lo, "prezzo_max": hi,
            "soglia_avviso": _number(p.get("soglia_avviso"), "threshold"), "alternative": alternatives,
            "accetta_simili": bool(p.get("accetta_simili", True)), "esclusi": _words(p.get("esclusi")), "pagine": pages}


def clean_channel(value: str) -> str:
    """Accetta nome, @nome o link t.me."""
    text = str(value).strip()
    text = re.sub(r"^(https?://)?(www\.)?(t\.me|telegram\.me)/(s/)?", "", text).lstrip("@").split("/")[0].split("?")[0]
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,31}", text):
        raise ValueError(f"channel: {value}")
    return text


def clean_custom_site(s: dict, general: dict) -> dict:
    url = str(s.get("url") or "").strip()
    if not re.match(r"https?://[^/\s]+", url) or "{q}" not in url:
        raise ValueError(f"url: {url}")
    name = str(s.get("nome") or "").strip() or re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    if s.get("valuta") and s["valuta"] not in catalog.CURRENCY_OF.values():
        raise ValueError(f"currency: {s['valuta']}")
    if s.get("paese") and s["paese"] not in catalog.COUNTRIES:
        raise ValueError(f"country: {s['paese']}")
    return {"id": s.get("id") or "custom_" + uuid.uuid4().hex[:8], "nome": name, "paese": s.get("paese") or general.get("paese"),
            "valuta": s.get("valuta") or general.get("valuta"), "tipo": s.get("tipo") if s.get("tipo") == "comparatore" else "negozio",
            "url": url, "negozio": "" if s.get("tipo") == "comparatore" else name, "selettori": None}


def apply_update(cfg: dict, update: dict) -> dict:
    """Controlla ciò che arriva dalla GUI e lo unisce alla configurazione. Lancia ValueError se qualcosa non va."""
    if "prodotti" in update:
        cfg["prodotti"] = [clean_product(p) for p in update["prodotti"]]
    if "generale" in update:
        g = {**cfg["generale"], **update["generale"]}
        if g["paese"] not in catalog.COUNTRIES:
            raise ValueError("country")
        every = int(g.get("intervallo_ore", 3))
        if not 1 <= every <= 24:
            raise ValueError("interval")
        g["intervallo_ore"] = every
        g["accept_language"] = catalog.ACCEPT_LANGUAGE.get(g["paese"])
        cfg["generale"] = g
    if "siti" in update:
        s = update["siti"]
        custom = [clean_custom_site(x, cfg["generale"]) for x in s.get("personalizzati", cfg["siti"].get("personalizzati") or [])]
        known = {x["id"] for x in catalog.SITES} | {x["id"] for x in custom}
        removed = [x for x in s.get("rimossi", cfg["siti"].get("rimossi") or []) if x in known]
        cfg["siti"] = {"attivi": [x for x in s.get("attivi", cfg["siti"].get("attivi") or []) if x in known and x not in removed],
                       "visti": cfg["siti"].get("visti") or [x["id"] for x in catalog.SITES], "rimossi": removed, "personalizzati": custom, "esiti": {**(cfg["siti"].get("esiti") or {}), **(s.get("esiti") or {})}}
    if "telegram" in update:
        canali = list(dict.fromkeys(clean_channel(c) for c in update["telegram"].get("canali") or []))
        cfg["telegram"] = {**cfg["telegram"], "canali": canali}
    if "ebay" in update:
        cfg["ebay"] = {**(cfg.get("ebay") or {}), **{k: str(update["ebay"][k]).strip() for k in ("app_id", "cert_id") if k in update["ebay"]}}
    if "notifiche" in update:
        cfg["notifiche"] = {**cfg["notifiche"], **update["notifiche"]}
    return cfg
