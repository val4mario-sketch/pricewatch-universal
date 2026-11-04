"""Cambi di riferimento della Banca Centrale Europea, salvati in dati/cambi.json. Niente account né chiavi."""
from __future__ import annotations

import json
import os
import re
import time
from datetime import date

import requests

from . import settings

URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
FRESH_HOURS = 12      # la BCE pubblica una volta al giorno
MAX_AGE_DAYS = 14     # oltre, meglio saltare il sito che confrontare prezzi con un cambio vecchio


def _path():
    return settings.DATA / "cambi.json"


def parse(xml: str) -> dict | None:
    day = re.search(r"time=['\"](\d{4}-\d{2}-\d{2})['\"]", xml)
    table = {c: float(r) for c, r in re.findall(r"currency=['\"]([A-Z]{3})['\"]\s+rate=['\"]([\d.]+)['\"]", xml) if float(r) > 0}
    if not day or len(table) < 10:
        return None
    return {"data": day.group(1), "tassi": {"EUR": 1.0, **table}}


def cached() -> dict | None:
    """I cambi salvati, se non sono troppo vecchi. Non usa la rete."""
    try:
        saved = json.loads(_path().read_text(encoding="utf-8"))
        if (date.today() - date.fromisoformat(saved["data"])).days <= MAX_AGE_DAYS and saved["tassi"]:
            return saved
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def get(log=print) -> dict | None:
    """Cambi aggiornati. Senza rete restano buoni quelli salvati; senza nemmeno quelli ritorna None."""
    saved = cached()
    if saved and time.time() - float(saved.get("scaricati") or 0) < FRESH_HOURS * 3600:
        return saved
    try:
        r = requests.get(URL, timeout=20)
        r.raise_for_status()
        table = parse(r.text)
        if table is None:
            raise ValueError("unreadable file")
    except (requests.RequestException, ValueError) as e:
        log(f"Exchange rates not updated ({type(e).__name__}); using: {saved['data'] if saved else 'none'}")
        return saved
    table["scaricati"] = time.time()
    settings.DATA.mkdir(parents=True, exist_ok=True)
    tmp = _path().with_suffix(".tmp")
    tmp.write_text(json.dumps(table), encoding="utf-8")
    os.replace(tmp, _path())
    return table


def factor(table: dict | None, source: str, target: str) -> float | None:
    """Per quanto moltiplicare un prezzo in `source` per averlo in `target`. None se il cambio non c'è."""
    if source == target:
        return 1.0
    rates_ = (table or {}).get("tassi") or {}
    if source not in rates_ or target not in rates_:
        return None
    return rates_[target] / rates_[source]
