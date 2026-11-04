"""Distingue l'offerta più affidabile dal semplice prezzo più basso."""
from __future__ import annotations

from collections import defaultdict

from .i18n import money, t

ANOMALY_RATIO = 0.6  # sotto il 60% del quartile basso delle offerte simili il prezzo è sospetto
ANOMALY_MIN_OTHERS = 3
LEVEL_ORDER = {"esatto": 0, "superiore": 0, "simile": 1, "incerto": 2}  # esatto e superiore vanno bene uguale: decide il prezzo
MEDIUM_FROM, LOW_FROM = 1, 4  # punti di rischio


def low_quartile(values: list[float]) -> float:
    """Un quarto delle offerte costa meno di così. La mediana si alza con kit, bundle e negozi lontani; questo no."""
    return sorted(values)[len(values) // 4]


def risk_points(o: dict) -> int:
    extra = o.get("extra") or {}
    points = int(bool(extra.get("estero"))) + int(bool(extra.get("valuta_orig"))) + int(bool(extra.get("browser")))
    points += int(extra.get("spec_non_lette") or 0)
    points += {"euristica": 1, "telegram": 2}.get(extra.get("metodo"), 0)
    points += 2 if o.get("level") == "incerto" else 0
    return points


def grade(o: dict) -> str:
    if o.get("dubbia"):
        return "bassa"
    points = risk_points(o)
    return "bassa" if points >= LOW_FROM else "media" if points >= MEDIUM_FROM else "alta"


def assess(offers: list[dict], cfg: dict) -> list[dict]:
    """Segna negozi da verificare e prezzi anomali. Si può richiamare più volte sulle stesse offerte."""
    shops = [s.lower() for s in (cfg.get("generale", {}).get("negozi_da_verificare") or [])]
    groups, same_code = defaultdict(list), defaultdict(list)
    for o in offers:
        groups[(o["component"], o.get("level"))].append(o["total"])
        code = (o.get("extra") or {}).get("codice")
        if code:
            same_code[(o["component"], code)].append(o["total"])
    for o in offers:
        warns = o.setdefault("warnings", [])
        extra = o.get("extra") or {}
        twins = same_code.get((o["component"], extra.get("codice")), [])
        o["stesso_modello"] = (len(twins), min(twins)) if len(twins) >= 2 else None
        o["dubbia"] = bool(extra.get("ia_dubbio") or extra.get("varianti"))
        if any(s in (o.get("shop") or "").lower() for s in shops):
            o["dubbia"] = True
            text = t(cfg, "w.shop")
            if text not in warns:
                warns.append(text)
        # il confronto più giusto è con lo stesso identico modello; senza abbastanza offerte, con la stessa categoria
        others = list(twins if len(twins) > ANOMALY_MIN_OTHERS else groups[(o["component"], o.get("level"))])
        others.remove(o["total"])
        if len(others) >= ANOMALY_MIN_OTHERS and o["total"] < ANOMALY_RATIO * low_quartile(others):
            o["dubbia"] = True
            text = t(cfg, "w.anomaly", price=money(cfg, low_quartile(others)))
            if text not in warns:
                warns.append(text)
        o["affidabilita"] = grade(o)
    return offers


def _rank(o: dict) -> tuple:
    extra = o.get("extra") or {}
    return bool(o.get("dubbia")), LEVEL_ORDER.get(o.get("level"), 3), bool(extra.get("dogana")), bool(extra.get("spec_non_lette")), o["total"]


def pick(offers: list[dict]) -> dict | None:
    """Senza dubbi, esatto o superiore, senza dogana, con le specifiche lette: tra questi il meno caro, anche se è all'estero."""
    return min(offers, key=_rank) if offers else None


def picks(offers: list[dict], cfg: dict) -> dict[str, dict]:
    assess(offers, cfg)
    by_comp = defaultdict(list)
    for o in offers:
        by_comp[o["component"]].append(o)
    return {cid: pick(offs) for cid, offs in by_comp.items()}
