"""Piccola IA locale (Ollama) per le offerte dubbie. Facoltativa: se non c'è, il giro va avanti con le sole regole.
Niente esce dal computer. L'IA non decide mai il prezzo, e un valore che non compare nel titolo viene ignorato."""
from __future__ import annotations

import hashlib
import json
import re
import time

import requests

from .i18n import t
from .rules import SYSTEM_WORDS, _has_word, judge_value, norm, spec_text, split_name

URL = "http://127.0.0.1:11434"
RECOMMENDED = "qwen2.5vl:3b"
KINDS = ("product", "accessory", "whole_computer", "used", "other_product")
SYSTEM = ("You check titles of shop listings. Judge only from the title and never guess. "
          "kind is: product = the item itself, new; accessory = a part or add-on for the item (cable, cover, bracket, cooler); "
          "whole_computer = a complete PC or laptop that merely contains the item; used = second hand or refurbished; "
          "other_product = a different item. "
          "values holds the numbers the title states for each requirement, null when it does not state them. "
          "Titles may be in any language.")


def status(timeout: float = 1.5) -> dict:
    """Ollama risponde? Quali modelli ha?"""
    try:
        r = requests.get(f"{URL}/api/tags", timeout=timeout)
        r.raise_for_status()
        return {"attiva": True, "modelli": [m["name"] for m in r.json().get("models", [])]}
    except (requests.RequestException, ValueError, KeyError):
        return {"attiva": False, "modelli": []}


def choose_model(wanted: str, installed: list[str]) -> str:
    if wanted and wanted in installed:
        return wanted
    return "" if wanted else (RECOMMENDED if RECOMMENDED in installed else (installed[0] if installed else ""))


def literal(value, title: str, unit: str) -> float | None:
    """Il numero deve stare accanto alla sua unità ("32 GB", "CL 30") o dentro un codice ("C30K"). Un numero qualsiasi non basta:
    nelle prove il modello leggeva "reso entro 30 giorni" come CL30."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    v, u = re.escape(f"{number:g}"), re.escape(unit)
    patterns = (rf"(?<![\d.,]){v}\s*-?\s*{u}(?![a-z])", rf"(?<![a-z]){u}\s*[:=-]?\s*{v}(?!\d)", rf"[a-z]{v}(?![\d.,])")
    return number if any(re.search(p, title, re.I) for p in patterns) else None


def ask(model: str, name: str, specs: list[dict], title: str, timeout: float = 60) -> dict | None:
    """Giudizio su un titolo, già ripulito. None se il modello non risponde in modo utilizzabile."""
    units = list(dict.fromkeys(str(s.get("unita") or s.get("nome")) for s in specs))
    schema = {"type": "object", "required": ["kind", "values"], "properties": {
        "kind": {"type": "string", "enum": list(KINDS)}, 
        "values": {"type": "object", "required": units, "properties": {u: {"type": ["number", "null"]} for u in units}}}}
    wanted = ", ".join(f"{s.get('unita') or s.get('nome')} {s.get('op')} {s.get('valore')}" for s in specs) or "none"
    body = {"model": model, "system": SYSTEM, "stream": False, "format": schema, "keep_alive": "2m",
            "options": {"temperature": 0, "num_predict": 80, "num_ctx": 1024},
            "prompt": f"Wanted model: {name}\nRequirements: {wanted}\nListing title: {title[:220]}"}
    try:
        r = requests.post(f"{URL}/api/generate", json=body, timeout=timeout)
        r.raise_for_status()
        data = json.loads(r.json()["response"])
    except (requests.RequestException, ValueError, KeyError):
        return None
    if data.get("kind") not in KINDS:
        return None
    values = data.get("values") if isinstance(data.get("values"), dict) else {}
    return {"kind": data["kind"],
            "values": {u: literal(values.get(u), title, u) for u in units}}


def timed(*args, **kw) -> tuple[dict | None, float]:
    start = time.time()
    return ask(*args, **kw), time.time() - start


def _doubtful(o: dict) -> bool:
    extra = o.get("extra") or {}
    # le regole riconoscono meglio le parole delle lingue con l'alfabeto latino
    return o.get("level") == "incerto" or bool(extra.get("spec_non_lette")) or re.search(r"[^\x00-\u024f]", o.get("title") or "") is not None


def _candidates(offers: list[dict], limit: int) -> list[dict]:
    """Le dubbie più alcune tra le migliori: prima i negozi del tuo Paese, dal prezzo più basso."""
    ranked = sorted(offers, key=lambda o: (bool((o.get("extra") or {}).get("estero")), o["total"]))
    top = [o for o in ranked if not _doubtful(o)][:3]
    return (top + [o for o in ranked if _doubtful(o)])[:limit]


def review(cfg: dict, rules, offers: list[dict], store, rejected: list[dict], log=print) -> list[dict]:
    """Controlla le offerte dubbie. Ritorna quelle che restano; le tolte finiscono tra le scartate."""
    g = cfg.get("generale", {})
    if not g.get("ia_attiva"):
        return offers
    st = status()
    model = choose_model(g.get("ia_modello") or "", st["modelli"])
    if not model:
        log("Local AI not available: rules only.")
        return offers
    deadline = time.time() + float(g.get("ia_max_sec", 300))
    limit = int(g.get("ia_max_offerte", 40))
    removed: set[int] = set()
    asked = from_cache = 0
    for cid, product in rules.components.items():
        core, name_specs = split_name(product.get("nome", ""))
        specs = [*name_specs, *(product.get("specifiche") or [])]
        specs = [s for s in specs if s.get("op") != "text"]
        for o in _candidates([x for x in offers if x["component"] == cid], limit):
            key = hashlib.sha1(json.dumps([model, core, specs, o["title"]], sort_keys=True).encode("utf-8")).hexdigest()
            answer = store.ai_get(key)
            if answer is None:
                if time.time() >= deadline:
                    continue
                answer = ask(model, core, specs, o["title"])
                if answer is None:
                    continue
                store.ai_put(key, answer)
                asked += 1
            else:
                from_cache += 1
            if not _apply(cfg, o, answer, core, specs, rejected):
                removed.add(id(o))
    log(f"Local AI ({model}): {asked} checked, {from_cache} from memory, {len(removed)} removed.")
    return [o for o in offers if id(o) not in removed]


def _discard(o: dict, reason: str, rejected: list[dict]):
    rejected.append({"component": o["component"], "title": o["title"][:200], "price": o["total"], "source": o.get("source"),
                     "reason": reason, "score": (o.get("extra") or {}).get("punteggio", 0)})


def _apply(cfg: dict, o: dict, answer: dict, core: str, specs: list[dict], rejected: list[dict]) -> bool:
    """Applica il giudizio. False se l'offerta va tolta."""
    extra = o.setdefault("extra", {})
    extra["ia"] = True
    kind = answer.get("kind")
    wants_computer = any(_has_word(w, norm(core)) for w in SYSTEM_WORDS)
    if kind in ("accessory", "whole_computer") and not (kind == "whole_computer" and wants_computer):
        label = t(cfg, f"ai.{kind}")
        if o.get("level") == "incerto":
            _discard(o, t(cfg, "r.ai", kind=label), rejected)
            return False
        # le regole la considerano buona: l'IA può sbagliare, quindi resta visibile ma non viene scelta
        extra["ia_dubbio"] = True
        text = t(cfg, "w.ai_kind", kind=label)
        if text not in o["warnings"]:
            o["warnings"].append(text)
    for spec in specs:
        unit = str(spec.get("unita") or spec.get("nome"))
        name = spec.get("nome") or unit
        missing = t(cfg, "w.spec_missing", name=name)
        value = (answer.get("values") or {}).get(unit)
        if value is None or missing not in o["warnings"]:
            continue
        state = judge_value(spec, float(value))
        shown = f"{float(value):g}"
        if state == "out":
            _discard(o, t(cfg, "r.ai_value", name=name, value=shown, wanted=spec_text(spec)), rejected)
            return False
        o["warnings"].remove(missing)
        extra["spec_non_lette"] = max(0, int(extra.get("spec_non_lette") or 0) - 1)
        o.setdefault("tags", []).append(t(cfg, "w.ai_value", name=name, value=shown))
    return True
