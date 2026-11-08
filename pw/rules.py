"""Rules for the products chosen in the GUI: decides whether an offer is exact, similar, better or to be discarded."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .i18n import money, t

_LEVELS = ("esatto", "superiore", "simile")

# Always discarded: the app looks for new products. These are words in several languages, compared with the normalized title.
GLOBAL_EXCLUDED = re.compile(
    r"\b(?:usat[oa]|seconda mano|ricondizionat\w*|rigenerat\w*|refurb\w*|renewed|used|pre ?owned|second hand|gebraucht\w*|"
    r"occasion|reacondicionad\w*|difettos\w*|defective|for parts|parts only|open box|b ware|scatola vuota|empty box|"
    r"generalüberholt\w*|defekt\w*|reconditionn\w*|seconde main|usad[oa]s?|segunda mano|segunda mão|recondicionad\w*|"
    r"tweedehands|gebruikt\w*|używan\w*|powystawow\w*|odnowion\w*|begagnad\w*|begagnat|brukt\w*|brugt\w*|použit\w*|repasovan\w*|"
    r"bazarov\w*|ikinci el|yenilenmiş|folosit\w*|resigilat\w*|használt|felújított|μεταχειρισμέν\w*|bekas|terpakai|משומש)\b", re.I)
# In scripts without spaces there are no word boundaries: it is enough to find them in the title.
EXCLUDED_NO_SPACES = re.compile(r"中古|整備済|ジャンク|二手|翻新|拆机|중고|리퍼|มือสอง|ใช้แล้ว")
# Accessories: discarded, unless the word is in the name of the product being searched for.
ACCESSORIES = ("cover", "custodia", "pellicola", "screen protector", "adattatore", "adapter", "cavo", "cable",
               "ricambio", "spare part", "replacement", "staffa", "bracket", "backplate", "riser", "holder",
               "supporto", "skin", "sticker", "bundle", "combo",
               "kabel", "halterung", "hülle", "schutzfolie", "ersatzteil", "adaptateur", "câble", "coque", "housse", "pièce détachée",
               "adaptador", "funda", "repuesto", "protector de pantalla", "capa", "cabo", "hoes", "houder", "beugel", "przejściówka",
               "etui", "uchwyt", "pokrowiec", "folia", "fodral", "hållare", "deksel", "kablo", "kılıf", "adaptör", "καλώδιο",
               "ケーブル", "変換", "カバー", "ブラケット", "ステッカー", "数据线", "转接", "支架", "保护壳", "贴纸", "케이블", "브라켓", "어댑터", "สายเคเบิล")
# Whole computers: with one of these names and a processor in the title, the card or component searched for is only a part.
SYSTEM_WORDS = ("komputer", "laptop", "notebook", "portatile", "portatil", "portátil", "gaming pc", "pc gaming", "pc da gaming", "pc gamer",
                "desktop pc", "pc desktop", "mini pc", "computer fisso", "gaming rechner", "komplett pc", "prebuilt", "pc portable",
                "ordinateur", "ordenador", "gamingdator", "bärbar dator", "dizüstü", "masaüstü", "bilgisayar", "počítač", "notebooku",
                "整机", "台式机", "组装机", "笔记本", "노트북", "데스크탑", "ノートpc", "ノートパソコン", "デスクトップ", "ゲーミングpc")
_CPU = re.compile(r"\b(?:core ?(?:ultra|i[3579])|i[3579] ?\d{4,5}|ryzen(?: ai)? ?[3579])")
_STORAGE = re.compile(r"\b(?:ssd|nvme|hdd)\b")

# Mutually convertible units: value in base units.
UNIT_FAMILIES = [
    {"g": 1, "gr": 1, "kg": 1e3, "oz": 28.3495, "lb": 453.592},
    {"b": 1e-9, "kb": 1e-6, "mb": 1e-3, "g": 1, "gb": 1, "tb": 1e3},  # "16G" in graphics card titles
    {"hz": 1, "khz": 1e3, "mhz": 1e6, "ghz": 1e9},
    {"mm": 1, "cm": 10, "m": 1000, "in": 25.4, "inch": 25.4, "pollici": 25.4, '"': 25.4},
    {"w": 1, "kw": 1000, "watt": 1},
    {"mah": 1, "ah": 1000},
    {"ml": 1, "l": 1000},
]


# Words that describe the product type but that many titles omit: they do not help recognize it.
GENERIC_WORDS = {"ram", "memoria", "memorie", "memory", "kit", "modulo", "moduli"}
_UNITS = "gb|tb|mb|mhz|ghz|hz|kw|w|mah|mm|cm"
# With memory, remove notebook and server versions and motherboards that mention it.
FAMILY_EXCLUDED = [(re.compile(r"\bddr\d"), re.compile(r"\b(?:so dimm|sodimm|laptop|notebook|ecc|rdimm|registered|scheda madre|motherboard|mainboard|"
                                                         r"[abxz]\d{3}\w*)\b"))]


def _french_units(title: str) -> str:
    """32 Go and 1 To are GB and TB. "To" only when capitalized: "2 to 1" is English."""
    return re.sub(r"(\d) ?To\b", r"\1 TB", re.sub(r"(\d) ?[Gg][Oo]\b", r"\1 GB", title))


def norm(title: str) -> str:
    """Comparable title: "32 GB" and "32GB" become equal, "2x16GB" also counts as 32gb, "6000MT/s" counts as 6000mhz."""
    t_ = _french_units(title or "").lower().replace("×", "x").replace("–", " ").replace("—", " ")
    t_ = re.sub(r"(\d) ?mt ?/ ?s\b", r"\1mhz", t_)
    t_ = re.sub(r"[-_/,;:()\[\]|®™'`]+", " ", t_)
    t_ = re.sub(r"\s+", " ", t_).strip()
    t_ = re.sub(rf"\b(\d+) ({_UNITS})\b", r"\1\2", t_)
    t_ = re.sub(r"\bcl (\d{2})\b", r"cl\1", t_)
    extra = [f"{int(n) * int(m)}{u}" for n, m, u in re.findall(r"\b(\d+) ?x ?(\d+)(gb|tb)\b", t_)]
    extra += [f"{int(m) * int(n)}gb" for m, n in re.findall(r"\b(\d+) ?g(?:b)? ?x ?(\d)\b", t_)]  # "16GBx2", "16Gx2"
    extra += [f"cl{c}" for c in re.findall(r"\bc(\d{2})\b", t_)]
    return " ".join([t_, *extra])


def _squeeze(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text)


def _has_word(word: str, text: str) -> bool:
    unit = f"(?:{_UNITS})?" if word.isdigit() else ""  # "6000" also applies to "6000mhz"
    return re.search(rf"(?<![a-z0-9]){re.escape(word)}{unit}(?![a-z0-9])", text) is not None


def _tokens(phrase: str) -> list[str]:
    return norm(phrase).split()


def _word_in(word: str, text: str) -> bool:
    """The word is present, even written apart or joined: "5070ti" in "5070 ti", "ti" in "rtx5070ti". "9900x" is not in "9900x3d"."""
    if _has_word(word, text):
        return True
    title = text.split()
    for size in (2, 3):
        if any("".join(title[i:i + size]) == word for i in range(len(title) - size + 1)):
            return True
    if len(word) < 2 or (word.isdigit() and len(word) < 3):
        return False
    return any(word in re.split(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", x) for x in title)


def matches_phrase(phrase: str, text: str) -> bool:
    """All words present, in any order; "5070 ti" also matches "5070ti" and vice versa."""
    words = _tokens(phrase)
    if not words:
        return False
    if all(_word_in(w, text) for w in words):
        return True
    squeezed = _squeeze(phrase.lower())
    return len(words) > 1 and any(_has_word(squeezed, w) for w in text.split())


PRICE_FRACTION = 0.25
UNCERTAIN_MIN = 60  # below this score the offer is discarded, even if it contains the model number


def _is_model_number(word: str) -> bool:
    return len(word) >= 2 and re.search(r"\d", word) is not None


def match_score(name: str, text: str) -> tuple[int, bool]:
    """How much the title resembles the name, from 0 to 100, like a search engine score: model numbers weigh
    three times the other words, and a nearly identical word counts. Also says whether a model number is missing."""
    words = _tokens(name)
    if not words:
        return 0, True
    title_words = text.split()
    got = total = 0
    model_missing = False
    for w in words:
        heavy = _is_model_number(w)
        weight = 3 if heavy else 1
        total += weight
        if heavy:
            found = _word_in(w, text)
            model_missing = model_missing or not found
        else:
            found = _word_in(w, text) or (len(w) >= 5 and any(SequenceMatcher(None, w, x).ratio() >= 0.85 for x in title_words))
        got += weight if found else 0
    return round(100 * got / total), model_missing


_CODE = re.compile(r"(?<![A-Z0-9-])[A-Z0-9][A-Z0-9-]{6,24}[A-Z0-9](?![A-Z0-9-])")
_NOT_A_CODE = re.compile(r"^(?:G?DDR|PC\d|RTX|GTX|RX\d|USB|PCIE|NVME|HDMI|UDIMM|DIMM|M\.?2|\d+X\d+)")


def model_code(title: str) -> str:
    """The manufacturer's code in the title (KD5AGU880-60A300F): the same code is the same product in every shop."""
    codes = [c for c in _CODE.findall((title or "").upper()) if re.search(r"\d", c) and re.search(r"[A-Z]", c) and not _NOT_A_CODE.match(c)
             and sum(ch.isdigit() for ch in c) >= 2 and sum(ch.isalpha() for ch in c) >= 2]
    return max(codes, key=len) if codes else ""


def split_name(name: str) -> tuple[str, list[dict]]:
    """Splits the name into what identifies the product and the values to treat as specifications.
    "32 GB ram ddr5 6000 CL30" becomes "ddr5" with ≥ 32 GB, ≥ 6000 MHz and ≤ CL 30, so CL28 or 64 GB count as better."""
    words, specs = _tokens(name), []
    is_memory = any(re.fullmatch(r"ddr\d", w) for w in words)
    core = []
    for w in words:
        size, speed, latency = re.fullmatch(r"(\d+)(gb|tb)", w), re.fullmatch(r"(\d{4})(?:mhz)?", w), re.fullmatch(r"cl(\d{2})", w)
        if size:
            specs.append({"nome": size.group(2).upper(), "op": "min", "valore": size.group(1), "unita": size.group(2).upper(), "margine_pct": 0})
        elif latency:
            specs.append({"nome": "CL", "op": "max", "valore": latency.group(1), "unita": "CL", "margine_pct": 0})
        elif speed and is_memory:
            specs.append({"nome": "MHz", "op": "min", "valore": speed.group(1), "unita": "MHz", "margine_pct": 0})
        elif w not in GENERIC_WORDS:
            core.append(w)
    return (" ".join(core), specs) if core else (name, [])


def _missing_words(phrase: str, text: str) -> list[str]:
    return [w for w in _tokens(phrase) if not _word_in(w, text)]


# ------------------------------------------------------------------ specifiche
def _unit_family(unit: str) -> dict | None:
    return next((f for f in UNIT_FAMILIES if unit in f), None)


def _num(text: str) -> float:
    return float(text.replace(",", "."))


def values_in_title(title: str, unit: str, label: str = "") -> list[float]:
    """Numbers in the title that refer to a unit, converted to the required unit. "2x16 GB" gives 16 and 32."""
    text = _french_units(title or "").lower().replace("×", "x").replace("mt/s", "mhz")
    unit = unit.strip().lower()
    number = r"\d+(?:[.,]\d+)?"
    if not unit:  # no unit: number right after or before the specification name
        name = re.escape(label.strip().lower())
        if not name:
            return []
        hits = re.findall(rf"{name}\s*[:=]?\s*({number})", text) + re.findall(rf"({number})\s*{name}\b", text)
        return [_num(h) for h in hits]
    family = _unit_family(unit)
    names = sorted(family, key=len, reverse=True) if family else [unit]
    alt = "|".join(re.escape(n) for n in names)
    found = []
    for mult, val, u in re.findall(rf"(?:(\d+)\s*x\s*)?({number})\s*-?\s*({alt})(?![a-z0-9])", text):
        factor = family[u] / family[unit] if family else 1
        found.append(_num(val) * factor)
        if mult:
            found.append(int(mult) * _num(val) * factor)
    # "16GBx2", "16Gx2": the number of modules written afterwards
    for val, u, mult in re.findall(rf"({number})\s*-?\s*({alt})\s*x\s*(\d)(?!\d)", text):
        found.append(int(mult) * _num(val) * (family[u] / family[unit] if family else 1))
    if family and "gb" in family:
        for val, mult in re.findall(rf"(?<![\d.,])({number})\s*x\s*(\d)\s*(?:\)|$|,|gb)", text):
            found.append(int(mult) * _num(val) * family["gb"] / family[unit])
    # unit written before the number: "CL30", "PCIe 5"
    if not family and unit.isalpha():
        found += [_num(v) for v in re.findall(rf"(?<![a-z]){re.escape(unit)}\s*-?\s*({number})", text)]
    if unit == "mhz" and "ddr" in text:  # "DDR5-6000", "DDR5 6400": memory states its speed without a unit
        found += [_num(v) for v in re.findall(r"(?<![\d.,])([3-9]\d{3})(?![\d.,a-z])", text)]
    if unit == "cl":  # "C30" in memory titles
        found += [_num(v) for v in re.findall(r"(?<![a-z0-9])c(\d{2})(?![a-z0-9])", text)]
    return found


def spec_text(spec: dict) -> str:
    op = {"min": "≥ ", "max": "≤ ", "eq": "= "}.get(spec.get("op"), "")
    return f"{op}{spec.get('valore', '')} {spec.get('unita') or ''}".strip()


def is_whole_system(text: str, wanted: str) -> str:
    """The word that shows a whole computer is being sold. Empty if the title is not one or if that is exactly what is wanted."""
    if not _CPU.search(text) or _CPU.search(wanted):
        return ""
    word = next((w for w in SYSTEM_WORDS if _has_word(w, text)), "")
    if word:
        return "" if _has_word(word, wanted) else word
    # processor, memory and disk listed in the same title
    wants_storage = _STORAGE.search(wanted)
    return "PC" if _STORAGE.search(text) and not wants_storage and len(re.findall(r"\d+ ?(?:gb|tb)\b", text)) >= 2 else ""


def has_variants(text: str) -> bool:
    """A title that lists several sizes or speeds in a row ("16gb 32gb", "5600mhz 6000mhz") is a multi-variant listing:
    the price shown is usually that of the cheapest, not the one you are looking for."""
    for a, b in re.findall(r"(?<![a-z0-9])(\d+(?:gb|tb|mhz)) (\d+(?:gb|tb|mhz))(?![a-z0-9])", text):
        if a != b and re.sub(r"\d", "", a)[-2:] == re.sub(r"\d", "", b)[-2:]:
            return True
    return re.search(r"(?<![\d.,])[3-9]\d{3} [3-9]\d{3}(?:mhz)?(?![a-z0-9])", text) is not None  # "4800/5600/6000MHz"


def _fmt(v: float, unit: str) -> str:
    return f"{v:g} {unit}".strip()


def judge_value(spec: dict, v: float) -> str:
    """A value compared with the specification: ok, better, near or out."""
    op = spec.get("op", "min")
    wanted = float(str(spec.get("valore", "")).replace(",", "."))
    margin = abs(float(spec.get("margine_pct") or 0)) / 100
    if op == "min":
        return "better" if v > wanted else "ok" if v == wanted else "near" if v >= wanted * (1 - margin) else "out"
    if op == "max":
        return "better" if v < wanted else "ok" if v == wanted else "near" if v <= wanted * (1 + margin) else "out"
    return "ok" if v == wanted else "near" if abs(v - wanted) <= wanted * margin else "out"


def check_spec(spec: dict, title: str, text: str) -> tuple[str, str]:
    """Ritorna (esito, valore letto). Esiti: ok, better, near, out, missing."""
    op = spec.get("op", "min")
    raw = str(spec.get("valore", "")).strip()
    if op == "text":
        return ("ok", raw) if matches_phrase(raw, text) else ("missing", "")
    try:
        wanted = float(raw.replace(",", "."))
    except ValueError:
        return "missing", ""
    unit = spec.get("unita") or ""
    values = values_in_title(title, unit, spec.get("nome", ""))
    if not values:
        return "missing", ""
    order = {"ok": 0, "better": 1, "near": 2, "out": 3}
    best = min(values, key=lambda v: (order[judge_value(spec, v)], abs(v - wanted)))
    return judge_value(spec, best), _fmt(best, unit)


# ------------------------------------------------------------------ decisione
@dataclass
class Decision:
    ok: bool
    component: str | None = None
    model: str | None = None
    level: str | None = None
    price: float | None = None
    total: float | None = None
    shipping: float | None = None
    warnings: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    reason: str = ""
    unread: int = 0  # requested specifications the title does not state
    score: int = 100  # similarity of the title to the name
    variants: bool = False  # the price may belong to another variant


class Rules:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.components = {p["id"]: p for p in cfg.get("prodotti", []) if p.get("attivo", True)}

    def name(self, cid: str) -> str:
        return self.components[cid].get("nome", cid)

    def _identify(self, product: dict, text: str) -> tuple[str, str, list[str]] | None:
        """Starting level, recognized model name, warnings. None if unrelated."""
        wanted = product.get("nome", "")
        cfg = self.cfg
        alternatives = sorted(product.get("alternative") or [], key=lambda a: -len(_tokens(a.get("testo", ""))))
        exact = matches_phrase(wanted, text)
        for alt in alternatives:  # "RTX 5070 Ti" among the alternatives must not count as an exact "RTX 5070"
            name = alt.get("testo", "")
            longer = len(_tokens(name)) > len(_tokens(wanted))
            if matches_phrase(name, text) and (not exact or longer):
                level = alt.get("tipo") if alt.get("tipo") in _LEVELS else "simile"
                return level, name, [t(cfg, "w.alt", name=name)]
        if exact:
            return "esatto", wanted, []
        if not product.get("accetta_simili", True):
            return None
        # Automatic similar: the name is at least 3 words long and only one is missing, which is neither the first (brand or
        # family) nor a model number: "RTX 5070" is close to "RTX 5070 Ti", "RTX 3060 Ti" is not.
        words = _tokens(wanted)
        missing = _missing_words(wanted, text)
        if len(words) >= 3 and len(missing) == 1 and missing[0] != words[0] and not re.search(r"\d", missing[0]):
            return "simile", wanted, [t(cfg, "w.similar_name", found=" ".join(w for w in words if w != missing[0]), wanted=wanted)]
        # Uncertain: similar enough and no model number missing. It stays visible at the bottom and is not chosen if there is something else.
        score, model_missing = match_score(wanted, text)
        if len(words) >= 2 and not model_missing and score >= UNCERTAIN_MIN:
            return "incerto", wanted, [t(cfg, "w.uncertain", score=score)]
        return None

    def classify(self, title: str, prices: list[float], shipping=None, total=None, hint: str | None = None) -> Decision:
        d = self._judge(title, prices, shipping, total, hint)
        product = self.components.get(hint)
        if product is not None:
            d.score = match_score(split_name(product.get("nome", ""))[0], norm(title))[0]
        return d

    def _judge(self, title: str, prices: list[float], shipping=None, total=None, hint: str | None = None) -> Decision:
        product = self.components.get(hint)
        if product is None:
            return Decision(False, reason=t(self.cfg, "r.not_matching"))
        cid, cfg, text = product["id"], self.cfg, norm(title)
        wanted = norm(product.get("nome", ""))
        hit = GLOBAL_EXCLUDED.search(text) or EXCLUDED_NO_SPACES.search(text)
        if hit:
            return Decision(False, cid, reason=t(cfg, "r.excluded", word=hit.group(0)))
        for word in ACCESSORIES:
            if _has_word(word, text) and not _has_word(word, wanted):
                return Decision(False, cid, reason=t(cfg, "r.excluded", word=word))
        for trigger, excluded in FAMILY_EXCLUDED:
            hit = trigger.search(wanted) and excluded.search(text)
            if hit and not excluded.search(wanted):
                return Decision(False, cid, reason=t(cfg, "r.excluded", word=hit.group(0)))
        system = is_whole_system(text, wanted)
        if system:
            return Decision(False, cid, reason=t(cfg, "r.system", word=system))
        for word in product.get("esclusi") or []:
            if matches_phrase(word, text):
                return Decision(False, cid, reason=t(cfg, "r.excluded", word=word))
        core, name_specs = split_name(product.get("nome", ""))
        identified = self._identify({**product, "nome": core}, text)
        if identified is None:
            return Decision(False, cid, reason=t(cfg, "r.not_matching"))
        level, model, warns = identified
        model = product.get("nome", "") if model == core else model
        warns = list(warns)
        own_units = {str(s.get("unita") or "").lower() for s in product.get("specifiche") or []}
        name_specs = [s for s in name_specs if s["unita"].lower() not in own_units]
        tags = []
        near = better = False
        unread = 0
        for spec in [*name_specs, *(product.get("specifiche") or [])]:
            name, wanted_txt = spec.get("nome") or spec.get("unita") or "?", spec_text(spec)
            state, value = check_spec(spec, title, text)
            if state == "out":
                return Decision(False, cid, model, reason=t(cfg, "r.spec_out", name=name, value=value, wanted=wanted_txt))
            if state == "missing":
                unread += 1
                warns.append(t(cfg, "w.spec_missing", name=name))
            elif state == "near":
                near = True
                warns.append(t(cfg, "w.spec_near", name=name, value=value, wanted=wanted_txt))
            elif state == "better":
                better = True
                tags.append(t(cfg, "w.spec_better", name=name, value=value, wanted=wanted_txt))
        if near and level != "incerto":
            level = "simile"
        elif better and level == "esatto":
            level = "superiore"
        # next to the price, shops also write price per GB, instalments and discounts: those small numbers are not the price
        prices = [p for p in prices if p >= PRICE_FRACTION * max(prices)] if prices else prices
        lo = float(product.get("prezzo_min") or 0)
        hi = float(product.get("prezzo_max") or 1e12)
        valid = [p for p in prices if lo <= p <= hi]
        if not valid:
            if not prices:
                return Decision(False, cid, model, reason=t(cfg, "r.no_price"))
            return Decision(False, cid, model, reason=t(cfg, "r.price", lo=money(cfg, lo), hi=money(cfg, product.get("prezzo_max"))))
        price = min(valid)
        tot = price + shipping if shipping is not None else price
        if total is not None and price <= total <= price * 1.25:
            tot = total
            shipping = round(total - price, 2)
        variants = has_variants(text)
        if variants:
            warns.append(t(cfg, "w.variants"))
        return Decision(True, cid, model, level, price, round(tot, 2), shipping, warns, tags, unread=unread, variants=variants)
