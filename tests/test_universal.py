import json
import os
import sys
import tempfile
import time

import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["PW_DATA"] = tempfile.mkdtemp()
os.environ["PW_TASK_NAME"] = "PriceWatch Universale Test"
from pw import ai, catalog, ebay, extract, notify, quality, rates, report, runner, schedule, settings  # noqa: E402
from pw.i18n import t as t_i18n  # noqa: E402
from pw.fetch import Page, looks_blocked  # noqa: E402
from pw.rules import Rules, check_spec, match_score, model_code, norm, split_name, values_in_title  # noqa: E402
from pw.store import Store  # noqa: E402

CFG = {"generale": {"lingua": "it", "valuta": "EUR", "paese": "IT", "negozi_da_verificare": ["aliexpress"]}, "prodotti": []}


def product(**kw):
    return settings.clean_product({"id": "p", "nome": "RTX 5070 Ti", **kw})


def judge(title, price=900, **kw):
    cfg = {**CFG, "prodotti": [product(**kw)]}
    return Rules(cfg).classify(title, [price], hint="p")


# ------------------------------------------------------------------ esatto, simile, superiore
def test_nome_esatto():
    d = judge("Gigabyte GeForce RTX 5070 Ti Windforce OC 16G")
    assert d.ok and d.level == "esatto"
    assert judge("MSI RTX5070Ti Ventus").level == "esatto", "senza spazi"


def test_simile_automatico_e_segnalato():
    d = judge("Gigabyte GeForce RTX 5070 Eagle")
    assert d.ok and d.level == "simile" and "simile" in d.warnings[0].lower()
    assert not judge("Gigabyte GeForce RTX 5070 Eagle", accetta_simili=False).ok


def test_niente_simile_se_manca_la_prima_parola_o_ne_mancano_due():
    assert judge("GeForce GT 5070 Ti").level == "incerto", "stays visible, but not as similar"
    assert not judge("GeForce RTX 4060").ok
    assert not judge("Septpenta RTX 3060 Ti").ok, "different model number"
    assert not judge("MSI RTX 5060 Ti").ok, "different model number"


def test_alternative_indicate():
    alts = [{"testo": "RTX 5080", "tipo": "superiore"}, {"testo": "RTX 4080 Super", "tipo": "simile"}]
    assert judge("ASUS RTX 5080 Prime", alternative=alts).level == "superiore"
    assert judge("Zotac RTX 4080 Super", alternative=alts).level == "simile"
    d = Rules({**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "RTX 5070", "alternative": [{"testo": "RTX 5070 Ti", "tipo": "superiore"}]})]})
    assert d.classify("Asus RTX 5070 Ti", [900], hint="p").level == "superiore", "the longest name wins"


def test_usato_e_accessori_scartati():
    assert not judge("RTX 5070 Ti usata come nuova").ok
    assert not judge("Refurbished RTX 5070 Ti").ok
    assert not judge("Backplate per RTX 5070 Ti").ok
    assert not judge("RTX 5070 Ti OEM", esclusi=["OEM"]).ok
    p = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "Cavo HDMI 2.1 Ugreen"})]}
    assert Rules(p).classify("Ugreen Cavo HDMI 2.1 2m", [15], hint="p").ok, "accessorio cercato apposta"


def test_prezzo_fuori_margine():
    assert not judge("RTX 5070 Ti", price=100, prezzo_min=500).ok
    assert not judge("RTX 5070 Ti", price=2000, prezzo_max=1500).ok
    assert judge("RTX 5070 Ti", price=1000, prezzo_min=500, prezzo_max=1500).ok


# ------------------------------------------------------------------ specifications and margins
RAM = {"nome": "Capacità", "op": "min", "valore": "16", "unita": "GB", "margine_pct": 25}


def test_specifica_soddisfatta_esatta():
    assert judge("RTX 5070 Ti 16GB", specifiche=[RAM]).level == "esatto"


def test_specifica_superiore_viene_segnalata():
    d = judge("RTX 5070 Ti 24 GB", specifiche=[RAM])
    assert d.level == "superiore" and "24 GB" in d.tags[0]


def test_specifica_nel_margine_diventa_simile():
    d = judge("RTX 5070 Ti 12GB", specifiche=[RAM])
    assert d.ok and d.level == "simile" and "dentro il margine" in d.warnings[0]


def test_specifica_fuori_margine_scartata():
    d = judge("RTX 5070 Ti 8GB", specifiche=[RAM])
    assert not d.ok and "fuori dal margine" in d.reason


def test_specifica_assente_avvisa_ma_resta():
    d = judge("RTX 5070 Ti OC", specifiche=[RAM])
    assert d.ok and d.level == "esatto" and "non indicata" in d.warnings[0]


def test_condizioni_massimo_uguale_e_testo():
    p = {"nome": "DDR5", "ricerca": ["DDR5"]}
    cl = {"nome": "CL", "op": "max", "valore": "30", "unita": "CL", "margine_pct": 10}
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", **p, "specifiche": [cl]})]}
    r = Rules(cfg)
    assert r.classify("Kingston DDR5 6000 CL28", [100], hint="p").level == "superiore"
    assert r.classify("Kingston DDR5 6000 CL30", [100], hint="p").level == "esatto"
    assert r.classify("Kingston DDR5 6000 CL32", [100], hint="p").level == "simile"
    assert not r.classify("Kingston DDR5 6000 CL40", [100], hint="p").ok
    eq = {"op": "eq", "valore": "27", "unita": "pollici", "margine_pct": 0}
    assert check_spec(eq, 'Monitor 27 pollici', norm('Monitor 27 pollici'))[0] == "ok"
    assert check_spec(eq, 'Monitor 32 pollici', norm('Monitor 32 pollici'))[0] == "out"
    assert check_spec({"op": "text", "valore": "HDMI 2.1"}, "x", norm("con HDMI 2.1"))[0] == "ok"


def test_unita_convertite_e_kit():
    assert values_in_title("SSD 2TB", "GB") == [2000]
    assert values_in_title("RTX 5070 16G Shadow", "GB") == [16]
    assert values_in_title("Mouse 60 g", "g") == [60]
    assert values_in_title("Kit 2x16GB", "GB") == [16, 32]
    assert values_in_title("CPU 3.8 GHz", "MHz") == [3800]
    assert values_in_title('Monitor 27" 144Hz', "inch") == [27]


# ------------------------------------------------------------------ valute
def test_prezzi_nelle_varie_valute():
    assert [p[0] for p in extract.prices_in("Now $1,299.99", "USD")] == [1299.99]
    assert [p[0] for p in extract.prices_in("£899.00 inc VAT", "GBP")] == [899.0]
    assert [p[0] for p in extract.prices_in("1.299,00 €", "EUR")] == [1299.0]
    assert [p[0] for p in extract.prices_in("¥128,000", "JPY")] == [128000.0]
    assert [p[0] for p in extract.prices_in("₹74,999", "INR")] == [74999.0]
    assert [p[0] for p in extract.prices_in("4 299 zł", "PLN")] == [4299.0]
    assert extract.prices_in("$100", "EUR") == [], "another currency is not a valid price"


def test_siti_in_altra_valuta_saltati():
    cfg = {**settings.defaults(), "generale": {**settings.defaults()["generale"], "valuta": "EUR", "paese": "IT"},
           "prodotti": [product()], "siti": {"attivi": ["amazon_it", "newegg"], "personalizzati": []}, "telegram": {"canali": ["prezzone"]}}
    tasks, skipped = runner.build_tasks(cfg)
    assert skipped == {"newegg": "currency"} and {x.source for x in tasks} == {"amazon_it", "telegram"}
    assert "t.me/s/prezzone?q=RTX+5070+Ti" in next(x.url for x in tasks if x.source == "telegram")
    assert all(x.product == "p" for x in tasks)


# ------------------------------------------------------------------ cambi
TABLE = {"data": "2026-10-30", "tassi": {"EUR": 1.0, "USD": 1.25, "GBP": 0.8, "JPY": 160.0}}
ECB = "<Cube time='2026-10-30'>" + "".join(f"<Cube currency='{c * 3}' rate='1.5'/>" for c in "ABCDEFGHIJ") + "<Cube currency='USD' rate='1.1172'/></Cube>"


def _tasks_result(item, site_currency="USD"):
    task = runner.Task("newegg", "ricerca", "https://x", "p", currency=site_currency, foreign=True)
    return runner.TaskResult(task, items=[item])


def _classify(item, site_currency="USD", table=TABLE, **kw):
    cfg = {**CFG, "prodotti": [product(**kw)]}
    return runner.classify_results(cfg, Rules(cfg), [_tasks_result(item, site_currency)], table)[0]


def test_cambio_tra_due_valute():
    assert rates.factor(TABLE, "USD", "EUR") == 0.8
    assert rates.factor(TABLE, "EUR", "GBP") == 0.8
    assert abs(rates.factor(TABLE, "USD", "GBP") - 0.64) < 1e-9, "passa dall'euro"
    assert rates.factor(None, "EUR", "EUR") == 1.0
    assert rates.factor(None, "USD", "EUR") is None and rates.factor(TABLE, "SEK", "EUR") is None


def test_lettura_file_bce():
    table = rates.parse(ECB)
    assert table["data"] == "2026-10-30" and table["tassi"]["USD"] == 1.1172 and table["tassi"]["EUR"] == 1.0
    assert rates.parse("<html>errore</html>") is None


def test_cambi_salvati_e_senza_rete():
    calls = []

    class Reply:
        text = ECB

        def raise_for_status(self):
            pass

    def online(url, timeout):
        calls.append(url)
        return Reply()

    def offline(url, timeout):
        raise rates.requests.ConnectionError("no")

    orig, today = rates.requests.get, rates.date
    rates._path().unlink(missing_ok=True)
    try:
        rates.requests.get = offline
        assert rates.get(lambda _: None) is None, "no network and no file"
        rates.requests.get = online
        fresh_day = {**rates.parse(ECB), "data": today.today().isoformat()}
        rates.parse, parse = (lambda _: dict(fresh_day)), rates.parse
        try:
            assert rates.get()["tassi"]["USD"] == 1.1172 and len(calls) == 1
            assert rates.get()["tassi"]["USD"] == 1.1172 and len(calls) == 1, "does not download again within 12 hours"
            saved = json.loads(rates._path().read_text(encoding="utf-8"))
            saved["scaricati"] = 0
            rates._path().write_text(json.dumps(saved), encoding="utf-8")
            rates.requests.get = offline
            assert rates.get(lambda _: None)["tassi"]["USD"] == 1.1172, "senza rete resta l'ultimo cambio"
            saved["data"] = "2020-01-01"
            rates._path().write_text(json.dumps(saved), encoding="utf-8")
            assert rates.cached() is None and rates.get(lambda _: None) is None, "cambio troppo vecchio"
        finally:
            rates.parse = parse
    finally:
        rates.requests.get = orig
        rates._path().unlink(missing_ok=True)


def test_sito_estero_entra_col_cambio():
    cfg = {**settings.defaults(), "generale": {**settings.defaults()["generale"], "valuta": "EUR", "paese": "IT"},
           "prodotti": [product()], "siti": {"attivi": ["amazon_it", "newegg"], "personalizzati": []}, "telegram": {"canali": []}}
    tasks, skipped = runner.build_tasks(cfg, table=TABLE)
    assert not skipped and {x.source: x.currency for x in tasks} == {"amazon_it": "EUR", "newegg": "USD"}


def test_prezzo_convertito_prima_di_giudicare():
    item = extract.RawItem("MSI RTX 5070 Ti", [1000.0], "https://x/1", "Newegg", 25.0)
    o = _classify(item)[0]
    assert (o["price"], o["shipping"], o["total"]) == (800.0, 20.0, 820.0)
    assert o["extra"]["valuta_orig"] == "USD" and o["extra"]["prezzo_orig"] == 1000.0
    w = next(x for x in o["warnings"] if "convertito" in x)
    assert "$1.000,00" in w and "30/10/2026" in w and "dogana" in w
    assert _classify(item, prezzo_max=700) == [], "the maximum applies in your currency"
    assert _classify(item, prezzo_min=900) == [], "the minimum applies in your currency"
    assert len(_classify(item, prezzo_max=900)) == 1


def test_stessa_valuta_nessuna_conversione():
    o = _classify(extract.RawItem("MSI RTX 5070 Ti", [900.0], "https://x/1", "S"), "EUR", None)[0]
    assert o["total"] == 900.0 and "valuta_orig" not in o["extra"] and not any("convertito" in w for w in o["warnings"])


def test_senza_cambio_niente_prezzo_inventato():
    assert _classify(extract.RawItem("MSI RTX 5070 Ti", [900.0], "https://x/1", "S"), "USD", None) == []


def test_vale_la_valuta_dichiarata_dalla_pagina():
    page = ('<script type="application/ld+json">[{"@type":"Product","name":"MSI RTX 5070 Ti","offers":{"price":"800","priceCurrency":"GBP"}},'
            '{"@type":"Product","name":"Asus RTX 5070 Ti","offers":{"price":"900","priceCurrency":"eur"}}]</script>')
    items = extract.jsonld_products(extract.BeautifulSoup(page, "lxml"), "https://x/")
    assert sorted(i.currency for i in items) == ["EUR", "GBP"]
    gbp = next(i for i in items if i.currency == "GBP")
    assert _classify(gbp, "EUR")[0]["total"] == 1000.0, "euro site showing pounds"
    assert _classify(gbp, "EUR", None) == []
    meta = '<h1>MSI RTX 5070 Ti</h1><meta property="product:price:amount" content="800"><meta property="product:price:currency" content="GBP">'
    assert extract.meta_product(extract.BeautifulSoup(meta, "lxml"), "https://x/").currency == "GBP"
    odd = '<script type="application/ld+json">{"@type":"Product","name":"MSI RTX 5070 Ti","offers":{"price":"800","priceCurrency":"€"}}</script>'
    assert extract.jsonld_products(extract.BeautifulSoup(odd, "lxml"), "https://x/")[0].currency == ""


def test_avviso_non_si_ripete_se_cambia_solo_il_cambio():
    sent = []
    orig = notify.send
    notify.send = lambda cfg, txt, **kw: sent.append(txt) or "ok"
    try:
        cfg = {**CFG, "prodotti": [product(soglia_avviso=1000)], "notifiche": {}}
        store, rules = Store(":memory:"), Rules(cfg)
        item = extract.RawItem("MSI RTX 5070 Ti", [800.0], "https://x/1", "S")
        for usd in (1.25, 1.2, 1.15):
            table = {"data": "2026-10-30", "tassi": {"EUR": 1.0, "USD": usd}}
            offers, _ = runner.classify_results(cfg, rules, [_tasks_result(item)], table)
            runner.alerts(cfg, rules, store, store.new_run(), offers, lambda _: None)
        assert len(sent) == 1 and "da $800,00" in sent[0], sent
    finally:
        notify.send = orig


def test_report_e_telegram_mostrano_il_prezzo_originale():
    cfg = {**CFG, "prodotti": [product()]}
    o = _classify(extract.RawItem("MSI RTX 5070 Ti", [1000.0], "https://x/1", "Newegg"))[0]
    store = _store([o])
    assert "800,00 €</b> · da $1.000,00" in report.telegram_summary(cfg, store)
    path = Path(os.environ["PW_DATA"]) / "r2.html"
    page = Path(report.generate(cfg, store, str(path))).read_text(encoding="utf-8")
    assert "≈ 800,00 €" in page and "$1.000,00" in page


def test_valuta_del_sito_aggiunto():
    g = {"paese": "IT", "valuta": "EUR"}
    assert settings.clean_custom_site({"url": "https://x.co.uk/s?q={q}", "valuta": "GBP"}, g)["valuta"] == "GBP"
    assert settings.clean_custom_site({"url": "https://x.it/s?q={q}"}, g)["valuta"] == "EUR"
    try:
        settings.clean_custom_site({"url": "https://x.it/s?q={q}", "valuta": "XXX"}, g)
        assert False
    except ValueError:
        pass


# ------------------------------------------------------------------ sites from all over the world
def test_al_primo_avvio_siti_di_tutto_il_mondo():
    active = catalog.default_active()
    paesi = {s["paese"] for s in catalog.SITES if s["id"] in active}
    assert "aliexpress" in active and {"IT", "WW", "US", "JP"} <= paesi
    assert settings.defaults()["generale"]["lingua"] == "en"


def test_negozio_internazionale_usa_la_tua_valuta():
    cfg = {**settings.defaults(), "generale": {**settings.defaults()["generale"], "valuta": "GBP", "paese": "GB"},
           "prodotti": [product()], "siti": {"attivi": ["aliexpress"], "personalizzati": []}, "telegram": {"canali": []}}
    tasks, skipped = runner.build_tasks(cfg)
    assert not skipped and tasks[0].currency == "GBP" and tasks[0].foreign


def test_togliere_e_ripristinare_un_sito():
    cfg = settings.defaults()
    cfg["siti"]["attivi"] = ["amazon_it", "aliexpress"]
    settings.apply_update(cfg, {"siti": {"rimossi": ["amazon_it"]}})
    assert cfg["siti"]["attivi"] == ["aliexpress"]
    row = next(s for s in catalog.site_list(cfg) if s["id"] == "amazon_it")
    assert row["rimosso"] and not row["attivo"]
    settings.apply_update(cfg, {"siti": {"rimossi": []}})
    assert not next(s for s in catalog.site_list(cfg) if s["id"] == "amazon_it")["rimosso"]


def test_sito_aggiunto_con_paese_e_valuta():
    g = {"paese": "IT", "valuta": "EUR"}
    site = settings.clean_custom_site({"url": "https://x.cn/s?q={q}", "paese": "CN", "valuta": "CNY"}, g)
    assert (site["paese"], site["valuta"]) == ("CN", "CNY")
    try:
        settings.clean_custom_site({"url": "https://x.cn/s?q={q}", "paese": "XX"}, g)
        assert False
    except ValueError:
        pass


def test_prezzi_nelle_valute_asiatiche():
    assert [p[0] for p in extract.prices_in("¥1,999", "CNY")] == [1999.0]
    assert [p[0] for p in extract.prices_in("1,999元", "CNY")] == [1999.0]
    assert [p[0] for p in extract.prices_in("1,234,000원", "KRW")] == [1234000.0]
    assert [p[0] for p in extract.prices_in("RM 3,299.00", "MYR")] == [3299.0]
    assert [p[0] for p in extract.prices_in("Rp 12.500.000", "IDR")] == [12500000.0]
    assert [p[0] for p in extract.prices_in("119 990 Ft", "HUF")] == [119990.0]


# ------------------------------------------------------------------ filters in several languages
def test_usato_e_accessori_in_altre_lingue():
    for title in ("MSI RTX 5070 Ti używana", "MSI RTX 5070 Ti gebraucht", "MSI RTX 5070 Ti reconditionnée", "MSI RTX 5070 Ti begagnad",
                  "MSI RTX 5070 Ti 中古", "二手 MSI RTX 5070 Ti", "MSI RTX 5070 Ti 중고", "Kabel RTX 5070 Ti", "RTX 5070 Ti ケーブル",
                  "Funda para RTX 5070 Ti", "RTX 5070 Ti 支架"):
        assert not judge(title).ok, title
    for title in ("MSI RTX 5070 Ti Ventus", "Gigabyte RTX 5070 Ti ゲーミング", "技嘉 RTX 5070 Ti 显卡", "Karta graficzna MSI RTX 5070 Ti"):
        assert judge(title).ok, title


def test_computer_intero_scartato():
    for title in ("Komputer Game X G100 Lite, Core i5-14400F, 32 GB, RTX 5070 Ti", "ASUS TUF Gaming Laptop Ryzen 7 RTX 5070 Ti",
                  "PC Gamer Ryzen 7 9700X RTX 5070 Ti", "MSI Aegis i7 14700F 32GB 1TB SSD RTX 5070 Ti", "拯救者 笔记本 i7 14700 RTX 5070 Ti"):
        d = judge(title)
        assert not d.ok and "Computer intero" in d.reason, title


def test_filtro_computer_non_tocca_i_componenti():
    assert judge("MSI RTX 5070 Ti for gaming pc").ok, "without a processor it is not a computer"
    assert judge("Case PC gaming RTX 5070 Ti ready").ok
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "Laptop Lenovo Legion"})]}
    assert Rules(cfg).classify("Laptop Lenovo Legion Core i7 14700HX", [900], hint="p").ok, "the laptop is what is wanted"
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "Ryzen 7 7800X3D"})]}
    assert Rules(cfg).classify("AMD Ryzen 7 7800X3D processore", [300], hint="p").ok
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "Samsung 990 Pro"})]}
    assert Rules(cfg).classify("Samsung 990 Pro SSD 2TB NVMe per notebook", [150], hint="p").ok


# ------------------------------------------------------------------ reliability
def test_gradi_di_affidabilita():
    cfg = {**CFG, "prodotti": [product()]}
    base = {"metodo": "selettori", "estero": False, "browser": False, "spec_non_lette": 0}
    offer = lambda **kw: {**_offer(1000), "extra": {**base, **kw}}  # noqa: E731
    assert quality.grade(offer()) == "alta"
    assert quality.grade(offer(estero=True)) == "media"
    assert quality.grade(offer(estero=True, valuta_orig="USD", browser=True)) == "media"
    assert quality.grade(offer(estero=True, valuta_orig="USD", browser=True, metodo="euristica")) == "bassa"
    assert quality.grade(offer(metodo="telegram")) == "media"
    assert quality.grade({**offer(), "dubbia": True}) == "bassa"
    offers = quality.assess([_offer(185), _offer(480), _offer(500), _offer(520)], cfg)
    assert offers[0]["affidabilita"] == "bassa" and offers[1]["affidabilita"] == "alta"


def test_a_parita_di_modello_vince_il_piu_affidabile():
    cfg = {**CFG, "prodotti": [product()]}
    near = {**_offer(1000), "extra": {"metodo": "selettori"}}
    far = {**_offer(900), "extra": {"estero": True, "valuta_orig": "USD", "dogana": True}}
    assert quality.picks([far, near], cfg)["p"]["total"] == 1000, "outside the EU the price is not complete"


def test_grado_in_report_e_telegram():
    cfg = {**CFG, "prodotti": [product()]}
    store = _store([{**_offer(1000), "extra": {"estero": True}}, _offer(1100)])
    txt = report.telegram_summary(cfg, store)
    assert "1.000,00 €</b> · Affidabilità media" in txt, "the cheapest EU shop wins and the grade says so"
    path = Path(os.environ["PW_DATA"]) / "r3.html"
    page = Path(report.generate(cfg, store, str(path))).read_text(encoding="utf-8")
    assert 'class="rel alta"' in page and 'class="rel media"' in page and "L'affidabilità dice" in page


def test_siti_col_browser_nello_stesso_giro():
    cfg = {**settings.defaults(), "generale": {**settings.defaults()["generale"], "valuta": "EUR", "paese": "IT"},
           "prodotti": [product()], "siti": {"attivi": ["joom", "amazon_it"], "personalizzati": []}, "telegram": {"canali": []}}
    orig = runner.Fetcher.browser_available
    try:
        runner.Fetcher.browser_available = staticmethod(lambda: True)
        tasks, skipped = runner.build_tasks(cfg)
        assert not skipped and {x.source: x.browser for x in tasks} == {"joom": True, "amazon_it": False}
        runner.Fetcher.browser_available = staticmethod(lambda: False)
        assert runner.build_tasks(cfg)[1] == {"joom": "browser"}
    finally:
        runner.Fetcher.browser_available = orig


def test_un_sito_col_browser_bloccato_non_ferma_gli_altri():
    class Fake:
        def __init__(self, cfg):
            pass

        def get(self, url, browser=False):
            return Page(url, 403, "", blocked=True) if "bad" in url else Page(url, 200, "<html></html>")

        def close(self):
            pass

    orig = runner.Fetcher
    runner.Fetcher = Fake
    try:
        tasks = [runner.Task("bad", "ricerca", f"https://bad.test/{i}", "p", browser=True) for i in range(4)]
        tasks += [runner.Task("good", "ricerca", f"https://good.test/{i}", "p", browser=True) for i in range(3)]
        res = runner.execute(CFG, tasks, lambda _: None)
    finally:
        runner.Fetcher = orig
    assert sum(r.skipped for r in res if r.task.source == "bad") == 2 and not any(r.skipped for r in res if r.task.source == "good")


def test_browser_piantato_non_ferma_il_giro():
    import pw.fetch as fetch
    script = Path(os.environ["PW_DATA"]) / "piantato.py"
    script.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    f, orig_file, orig_extra = fetch.Fetcher({"generale": {"timeout_sec": 0}}), fetch.__file__, fetch.BROWSER_EXTRA_SEC
    orig_with = fetch.Path.with_name
    try:
        fetch.BROWSER_EXTRA_SEC = -19
        fetch.Path.with_name = lambda self, name: script
        start = time.time()
        page = f._get_browser("https://x.test/")
    finally:
        fetch.Path.with_name, fetch.BROWSER_EXTRA_SEC = orig_with, orig_extra
    assert not page.ok and "no answer" in page.error and time.time() - start < 15


def test_comparatore_apre_le_schede_raggruppate():
    search = ('<a class="relevant_item" href="/schede/msi">MSI RTX 5070 Ti da 1.289,99 €</a>'
              '<a class="relevant_item" href="/schede/pny">PNY RTX 5070 Ti da 1.390,00 €</a>')
    offers = '<li class="o"><span class="t">{0} RTX 5070 Ti OC</span><span class="p">1.300,00 €</span><span class="s">eBay</span><a href="/goto/{0}">x</a></li>'
    pages = {"https://t.test/s": search, "https://t.test/schede/msi": offers.format("MSI"), "https://t.test/schede/pny": offers.format("PNY")}

    class Fake:
        def get(self, url, browser=False):
            return Page(url, 200, pages[url])

    sel = {"item": "li.o", "titolo": ".t", "prezzo": ".p", "negozio": ".s"}
    res = runner.run_task(Fake(), runner.Task("tp", "ricerca", "https://t.test/s", "p", sel=sel, expand="a.relevant_item"))
    assert len(res.pages) == 3 and sorted(i.title for i in res.items) == ["MSI RTX 5070 Ti OC", "PNY RTX 5070 Ti OC"]
    assert {i.shop for i in res.items} == {"eBay"}, "the real shop stays"
    assert [i.prices for i in res.items] == [[1300.0], [1300.0]], "not the 'from...' price of the product page"
    assert extract.card_links(search * 4, "https://t.test/", "a.relevant_item", 1) == ["https://t.test/schede/msi"]


def test_una_scheda_bloccata_non_ferma_il_comparatore():
    calls = []

    class Fake:
        def __init__(self, cfg):
            pass

        def get(self, url, browser=False):
            calls.append(url)
            if url.endswith("/s"):
                return Page(url, 200, '<a class="c" href="/a">x</a><a class="c" href="/b">y</a>')
            return Page(url, 403, "", blocked=True)

        def close(self):
            pass

    orig = runner.Fetcher
    runner.Fetcher = Fake
    try:
        tasks = [runner.Task("tp", "ricerca", f"https://t.test/{i}/s", "p", expand="a.c") for i in range(4)]
        res = runner.execute(CFG, tasks, lambda _: None)
    finally:
        runner.Fetcher = orig
    assert not any(r.skipped for r in res) and len(res) == 4


def test_siti_nuovi_si_attivano_ma_quelli_spenti_no():
    orig_status = catalog.tested_status
    settings.CONFIG.parent.mkdir(parents=True, exist_ok=True)
    catalog.tested_status = lambda: {"amazon_it": {"esito": "ok"}, "yeppon": {"esito": "ok"}, "conrad_it": {"esito": "ok"}, "fnac": {"esito": "bloccato"}}
    try:
        # old configuration, with no list of seen sites
        settings.CONFIG.write_text(yaml.safe_dump({"siti": {"attivi": ["amazon_it"]}}), encoding="utf-8")
        attivi = settings.load()["siti"]["attivi"]
        assert {"amazon_it", "yeppon", "conrad_it", "trovaprezzi"} <= set(attivi) and "fnac" not in attivi
        # the user turns off Yeppon and removes Conrad: they do not come back
        cfg = settings.load()
        settings.apply_update(cfg, {"siti": {"attivi": ["amazon_it"], "rimossi": ["conrad_it"]}})
        settings.save(cfg)
        attivi = settings.load()["siti"]["attivi"]
        assert attivi == ["amazon_it"], attivi
    finally:
        catalog.tested_status = orig_status
        settings.CONFIG.unlink(missing_ok=True)


def test_report_prima_i_negozi_senza_dogana():
    cfg = {**CFG, "prodotti": [product()]}
    store = _store([{**_offer(500, shop="Danawa"), "extra": {"estero": True, "dogana": True}}, _offer(1000, shop="Unieuro")])
    path = Path(os.environ["PW_DATA"]) / "r4.html"
    page = Path(report.generate(cfg, store, str(path))).read_text(encoding="utf-8")
    assert page.index("Unieuro") < page.index("Danawa")


RAM_NAME = "32 GB ram ddr5 6000 CL30"


def _ram(title, price=500):
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": RAM_NAME})]}
    return Rules(cfg).classify(title, [price], hint="p")


def test_ram_scritta_in_tanti_modi():
    for title in ("Patriot Viper Venom DDR5 32GB (2 x 16GB) 6000MT/s CL30 UDIMM", "Corsair Vengeance 2x16GB DDR5-6000 CL30",
                  "Kingston FURY Beast 32 GB 6000 MHz DDR5 CL 30", "Klevv Fit V DDR5 2×16GB 6000MHz C30"):
        d = _ram(title)
        assert d.ok and d.level == "esatto" and not d.unread, (title, d.level, d.reason, d.warnings)


def test_unita_francesi():
    assert not _ram("Kingston Fury Beast - 2 x 8 Go (16 Go) - DDR5 6000 MHz - CL30").ok, "16 GB, non 32"
    d = _ram("Klevv Fit V 32 Go DDR5-6000 CL30")
    assert d.ok and not d.unread
    assert values_in_title("Samsung SSD 1 To", "TB") == [1]
    assert values_in_title("Adapter 2 to 1 TB", "TB") == [1]


def test_ram_migliore_e_superiore():
    assert _ram("Klevv DDR5-6000 CL28 32GB Kit").level == "superiore"
    assert _ram("G.Skill DDR5 6400 CL30 2x16GB").level == "superiore"
    assert _ram("Corsair DDR5 6000 CL30 64GB (2x32GB)").ok


def test_ram_peggiore_scartata():
    for title in ("Corsair DDR5 6000 CL36 32GB", "Corsair DDR5 5600 CL30 32GB", "Corsair DDR5 6000 CL30 16GB (2x8GB)", "Corsair DDR4 3600 CL18 32GB"):
        assert not _ram(title).ok, title


def test_ram_senza_valore_nel_titolo_resta_da_verificare():
    d = _ram("Patriot Viper DDR5-6000 CL30 Black")
    assert d.ok and d.unread == 1 and any("GB" in w for w in d.warnings)


def test_ram_per_notebook_e_schede_madri_scartate():
    for title in ("Crucial 32GB DDR5 6000 CL30 SO-DIMM", "Kingston 32GB DDR5 6000 CL30 per notebook", "Kingston 32GB DDR5 6000 CL30 ECC",
                  "ASUS TUF B850-PLUS scheda madre DDR5 6000 CL30 32GB"):
        assert not _ram(title).ok, title


def test_valori_nel_nome_anche_per_altri_prodotti():
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "SSD 1TB"})]}
    rules = Rules(cfg)
    assert rules.classify("Samsung 990 Pro SSD 1TB NVMe", [100], hint="p").level == "esatto"
    assert rules.classify("Samsung 990 Pro SSD 2TB NVMe", [200], hint="p").level == "superiore"
    assert not rules.classify("Samsung SSD 500GB", [50], hint="p").ok
    assert not rules.classify("WD HDD 1TB", [50], hint="p").ok
    assert split_name("RTX 5070 Ti") == ("rtx 5070 ti", []), "a model number is not a specification"
    assert split_name("iPhone 16 Pro")[1] == []
    assert split_name("Ryzen 9 9900X")[1] == []
    assert split_name("32GB")[0] == "32GB"


def test_termine_di_ricerca_senza_parole_generiche():
    p = settings.clean_product({"id": "p", "nome": RAM_NAME})
    assert runner.search_terms(p) == ["32 GB ddr5 6000 CL30"]
    p = settings.clean_product({"id": "p", "nome": RAM_NAME, "ricerca": ["kit ram corsair", "DDR5 32GB"]})
    assert runner.search_terms(p) == ["kit ram corsair", "DDR5 32GB"], "terms written by you stay"


def test_prezzi_letti_male_tolti_ma_non_quelli_solo_bassi():
    offers = [_offer(t) for t in (0.19, 2.18, 185, 500, 520, 540, 560)]
    assert [o["total"] for o in runner.drop_misread(offers)] == [185, 500, 520, 540, 560], "185 stays: the anomaly flags it"
    few = [_offer(t) for t in (2, 500, 520)]
    assert len(runner.drop_misread(few)) == 3, "with few offers it cannot be said"


def test_punteggio_e_livello_incerto():
    assert match_score("rtx 5070 ti", norm("MSI RTX 5070 Ti"))[0] == 100
    assert match_score("rtx 5070 ti", norm("RTX 3060 Ti"))[1], "the model number is missing"
    assert match_score("rtx 5070 ti", norm("GeForce RTX5070Ti"))[1] is False
    d = judge("GeForce 5070 16G")
    assert d.ok and d.level == "incerto" and any("verifica" in w for w in d.warnings)
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "iPhone 16 Pro"})]}
    assert not Rules(cfg).classify("Apple iPhone 15 Pro", [900], hint="p").ok, "different model number"
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "Ryzen 9 9900X"})]}
    assert Rules(cfg).classify("AMD 9900X CPU tray", [300], hint="p").level == "incerto"
    assert not Rules(cfg).classify("AMD Ryzen 9 9950X", [300], hint="p").ok
    assert Rules({**CFG, "prodotti": [product(accetta_simili=False)]}).classify("GeForce 5070 16G", [900], hint="p").ok is False


def test_parola_scritta_quasi_uguale():
    assert match_score("sony headphones wireless", norm("Sony headphone wirelesss"))[0] == 100


def test_incerto_scelto_solo_se_non_c_e_altro():
    cfg = {**CFG, "prodotti": [product()]}
    assert quality.picks([_offer(800, "incerto"), _offer(1000)], cfg)["p"]["total"] == 1000
    only = [_offer(800, "incerto")]
    assert quality.picks(only, cfg)["p"]["level"] == "incerto" and only[0]["affidabilita"] == "media"
    txt = report.telegram_summary(cfg, _store([_offer(800, "incerto"), _offer(1000)]))
    assert "Più basso" not in txt, "an uncertain offer is not the price to beat"


def test_codice_del_produttore():
    assert model_code("Klevv Fit V 32GB DDR5-6000 CL30 (KD5AGU880-60A300F)") == "KD5AGU880-60A300F"
    assert model_code("Patriot Viper Venom 32GB Kit DDR5-6000 CL30 (PVV532G600C30K)") == "PVV532G600C30K"
    assert model_code("Samsung 990 PRO MZ-V9P1T0BW SSD") == "MZ-V9P1T0BW"
    for title in ("Corsair Vengeance DDR5-6000 32GB", "MSI RTX5070TI Ventus", "PC5-48000 memory", "Gaming OC Edition 2X16GB"):
        assert model_code(title) == "", title


def test_stesso_modello_e_prezzo_anomalo_per_modello():
    cfg = {**CFG, "prodotti": [product()]}
    twin = lambda v: {**_offer(v), "extra": {"codice": "KD5AGU880"}}  # noqa: E731
    offers = [twin(300), twin(800), twin(820), twin(840), _offer(290), _offer(300), _offer(310), _offer(320)]
    quality.assess(offers, cfg)
    assert offers[0]["dubbia"] and any("anomalo" in w for w in offers[0]["warnings"]), "low for that model, even if not for the category"
    assert offers[1]["stesso_modello"] == (4, 300)
    assert offers[4]["stesso_modello"] is None
    store = _store([twin(800), twin(820)])
    page = Path(report.generate(cfg, store, str(Path(os.environ["PW_DATA"]) / "r5.html"))).read_text(encoding="utf-8")
    assert "Stesso modello: 2 offerte" in page


def test_scartate_salvate_col_motivo():
    cfg = {**CFG, "prodotti": [product()]}
    out = []
    items = [extract.RawItem("MSI RTX 5070 Ti", [900.0], "https://x/1", "S"), extract.RawItem("Cavo RTX 5070 Ti", [20.0], "https://x/2", "S"),
             extract.RawItem("RTX 3060 Ti", [300.0], "https://x/3", "S")]
    task = runner.Task("s", "ricerca", "https://x", "p")
    offers, _ = runner.classify_results(cfg, Rules(cfg), [runner.TaskResult(task, items=items)], None, out)
    assert len(offers) == 1 and {r["title"] for r in out} == {"Cavo RTX 5070 Ti", "RTX 3060 Ti"}
    store = _store(offers)
    run_id = store.last_run()["id"]
    store.add_discarded(run_id, out)
    n, rows = store.discarded_of_run(run_id, "p")
    assert n == 2 and rows[0]["title"] == "Cavo RTX 5070 Ti", "closest first"
    page = Path(report.generate(cfg, store, str(Path(os.environ["PW_DATA"]) / "r6.html"))).read_text(encoding="utf-8")
    assert "Offerte scartate: 2" in page and "RTX 3060 Ti" in page and "cavo" in page


def _ai_setup(answers):
    calls = []

    def fake_ask(model, name, specs, title, timeout=60):
        calls.append(title)
        return answers.get(title)

    orig = ai.status, ai.ask
    ai.status, ai.ask = (lambda timeout=1.5: {"attiva": True, "modelli": ["m"]}), fake_ask
    return calls, orig


def _ai_offer(total, title, level="esatto", **extra):
    return {**_offer(total, level), "title": title, "warnings": [], "extra": {"estero": False, **extra}}


AI_CFG = {"generale": {"lingua": "it", "valuta": "EUR", "paese": "IT", "ia_attiva": True, "ia_modello": "", "ia_max_offerte": 40, "ia_max_sec": 300},
          "prodotti": [settings.clean_product({"id": "p", "nome": RAM_NAME})]}


def test_ia_toglie_gli_incerti_e_segna_gli_altri():
    answers = {"Dubbia": {"kind": "accessory", "values": {}}, "Buona": {"kind": "whole_computer", "values": {}}, "Vera": {"kind": "product", "values": {}}}
    calls, orig = _ai_setup(answers)
    try:
        rules, out = Rules(AI_CFG), []
        offers = [_ai_offer(100, "Dubbia", "incerto"), _ai_offer(200, "Buona", spec_non_lette=1), _ai_offer(300, "Vera", "incerto")]
        kept = ai.review(AI_CFG, rules, offers, Store(":memory:"), out, lambda _: None)
    finally:
        ai.status, ai.ask = orig
    assert [o["title"] for o in kept] == ["Buona", "Vera"], "the uncertain accessory is removed"
    assert out[0]["title"] == "Dubbia" and "accessorio" in out[0]["reason"]
    good = kept[0]
    assert good["extra"]["ia_dubbio"] and any("computer intero" in w for w in good["warnings"])
    quality.assess(kept, AI_CFG)
    assert good["dubbia"] and good["affidabilita"] == "bassa"
    assert kept[1]["extra"]["ia"] and kept[1]["level"] == "incerto", "the AI does not promote: the rules decide the model"


def test_ia_legge_i_valori():
    missing = t_i18n(AI_CFG, "w.spec_missing", name="CL")
    answers = {"Fuori": {"kind": "product", "values": {"CL": 36.0}}, "Dentro": {"kind": "product", "values": {"CL": 30.0}}, "Nulla": {"kind": "product", "values": {"CL": None}}}
    calls, orig = _ai_setup(answers)
    try:
        offers = [{**_ai_offer(v, n, spec_non_lette=1), "warnings": [missing]} for v, n in ((100, "Fuori"), (200, "Dentro"), (300, "Nulla"))]
        out = []
        kept = ai.review(AI_CFG, Rules(AI_CFG), offers, Store(":memory:"), out, lambda _: None)
    finally:
        ai.status, ai.ask = orig
    assert [o["title"] for o in kept] == ["Dentro", "Nulla"] and "CL 36" in out[0]["reason"]
    assert kept[0]["extra"]["spec_non_lette"] == 0 and missing not in kept[0]["warnings"] and any("IA" in x for x in kept[0]["tags"])
    assert kept[1]["extra"]["spec_non_lette"] == 1 and missing in kept[1]["warnings"]


def test_ia_non_ripete_i_titoli_e_rispetta_i_limiti():
    calls, orig = _ai_setup({f"T{i}": {"kind": "product", "values": {}} for i in range(6)})
    try:
        cfg = {**AI_CFG, "generale": {**AI_CFG["generale"], "ia_max_offerte": 2}}
        store = Store(":memory:")
        ai.review(cfg, Rules(cfg), [_ai_offer(100 + i, f"T{i}", "incerto") for i in range(6)], store, [], lambda _: None)
        assert len(calls) == 2, "maximum per product"
        ai.review(cfg, Rules(cfg), [_ai_offer(100 + i, f"T{i}", "incerto") for i in range(2)], store, [], lambda _: None)
        assert len(calls) == 2, "already seen"
        cfg0 = {**cfg, "generale": {**cfg["generale"], "ia_max_sec": 0, "ia_max_offerte": 40}}
        ai.review(cfg0, Rules(cfg0), [_ai_offer(100 + i, f"T{i}", "incerto") for i in range(2, 6)], store, [], lambda _: None)
        assert len(calls) == 2, "tempo finito"
    finally:
        ai.status, ai.ask = orig


def test_senza_ollama_il_giro_continua():
    orig = ai.status
    ai.status = lambda timeout=1.5: {"attiva": False, "modelli": []}
    try:
        offers = [_ai_offer(100, "X", "incerto")]
        assert ai.review(AI_CFG, Rules(AI_CFG), offers, Store(":memory:"), [], lambda _: None) == offers
        off = {**AI_CFG, "generale": {**AI_CFG["generale"], "ia_attiva": False}}
        assert ai.review(off, Rules(off), offers, Store(":memory:"), [], lambda _: None) == offers
    finally:
        ai.status = orig


def test_valore_inventato_dall_ia_ignorato():
    assert ai.literal(36, "Corsair CMH32GX5M2E6000C36 32GB", "CL") == 36, "the manufacturer's code can really indicate it"
    assert ai.literal(30, "Patriot Viper PVV532G600C30K", "CL") == 30
    assert ai.literal(30, "DDR5 6000 CL 30", "CL") == 30
    assert ai.literal(32, "Corsair 32 GB DDR5", "GB") == 32
    assert ai.literal(28, "DDR5 6000 CL30", "CL") is None
    assert ai.literal(30, "Crucial 32GB DDR5 reso entro 30 giorni", "CL") is None, "any number will not do"
    assert ai.literal(32, "G.Skill Trident DDR5 - Kit - 32", "GB") is None
    assert ai.literal(None, "x", "CL") is None and ai.literal("boh", "x", "CL") is None


def test_nome_scritto_attaccato_o_staccato():
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "rtx 5070ti"})]}
    rules = Rules(cfg)
    for title in ("MSI GeForce RTX 5070 Ti Ventus", "ASUS Prime RTX5070TI OC", "Gigabyte RTX 5070Ti Eagle", "PNY RTX 5070TI 16GB"):
        assert rules.classify(title, [1300], hint="p").level == "esatto", title
    for title in ("MSI RTX 5070 Ventus 12G", "MSI RTX 5060 Ti"):
        assert rules.classify(title, [900], hint="p").level != "esatto", title
    assert judge("ASUS Prime RTX5070TI OC").level == "esatto"
    assert judge("Gigabyte RTX 5070Ti Eagle").level == "esatto"
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": "Ryzen 9 9900X"})]}
    rules = Rules(cfg)
    assert rules.classify("AMD Ryzen 9 9900X box", [300], hint="p").level == "esatto"
    assert not rules.classify("AMD Ryzen 9 9900X3D", [500], hint="p").ok, "un altro processore"
    assert runner.search_terms(settings.clean_product({"id": "p", "nome": "rtx 5070ti"})) == ["rtx 5070 ti"]
    assert runner.search_terms(settings.clean_product({"id": "p", "nome": "Ryzen 9 9900X"})) == ["Ryzen 9 9900X"]


def test_prezzo_al_gb_e_rate_non_sono_il_prezzo():
    cfg = {**CFG, "prodotti": [settings.clean_product({"id": "p", "nome": RAM_NAME})]}
    d = Rules(cfg).classify("goodram IRDM RGB UDIMM 32GB Kit, DDR5-6000, CL30-38-38", [15.25, 487.95], hint="p")
    assert d.price == 487.95
    d = Rules(cfg).classify("Corsair 32GB DDR5-6000 CL30", [529.0, 649.0], hint="p")
    assert d.price == 529.0, "discount: the low price applies"


def test_i_prezzi_veri_non_sono_anomali_se_ci_sono_kit_cari():
    cfg = {**CFG, "prodotti": [product()]}
    offers = [_offer(t) for t in (319, 334, 355, 379, 420, 450, 600, 650, 700, 800, 900, 1000, 1100, 1200)]
    quality.assess(offers, cfg)
    assert not any(o["dubbia"] for o in offers), "the median is high, but these prices are not suspicious"
    offers = [_offer(t) for t in (185, 319, 334, 355, 379, 420, 450, 600, 650, 700)]
    quality.assess(offers, cfg)
    assert offers[0]["dubbia"] and not offers[1]["dubbia"]


def test_negozio_ue_compete_col_prezzo():
    cfg = {**CFG, "prodotti": [product()]}
    home = {**_offer(355), "extra": {}}
    german = {**_offer(334), "extra": {"estero": True}}
    far = {**_offer(300), "extra": {"estero": True, "dogana": True}}
    assert quality.picks([home, german, far], cfg)["p"]["total"] == 334
    better = {**_offer(320, "superiore"), "extra": {}}
    assert quality.pick([home, german, better])["total"] == 320, "better and cheaper"
    unread = {**_offer(310), "extra": {"spec_non_lette": 1}}
    assert quality.pick([home, unread])["total"] == 355, "with the specifications read first"
    settings_cfg = {**settings.defaults(), "generale": {**settings.defaults()["generale"], "valuta": "EUR", "paese": "IT"},
                    "prodotti": [product()], "siti": {"attivi": ["amazon_de", "scan"], "personalizzati": []}, "telegram": {"canali": []}}
    tasks = runner.build_tasks(settings_cfg, table=TABLE)[0]
    assert {x.source: x.customs for x in tasks} == {"amazon_de": False, "scan": True}
    table = {**TABLE, "tassi": {**TABLE["tassi"]}}
    tasks = runner.build_tasks({**settings_cfg, "generale": {**settings_cfg["generale"], "valuta": "GBP", "paese": "GB"}}, table=table)[0]
    assert {x.source: x.customs for x in tasks} == {"amazon_de": True, "scan": False}


def test_marchi_cinesi_su_aliexpress():
    base = settings.defaults()
    cfg = {**base, "generale": {**base["generale"], "valuta": "EUR", "paese": "IT"}, "siti": {"attivi": ["aliexpress", "amazon_it"], "personalizzati": []},
           "telegram": {"canali": []}, "prodotti": [settings.clean_product({"id": "r", "nome": RAM_NAME})]}
    tasks = runner.build_tasks(cfg)[0]
    assert [x.source for x in tasks].count("amazon_it") == 1, "the other sites get no extra requests"
    ali = [x.query for x in tasks if x.source == "aliexpress"]
    assert len(ali) == 6 and "KingBank 32 GB ddr5 6000 CL30" in ali
    for name, n in (("SSD 1TB", 6), ("Corsair ddr5 32GB", 1), ("RTX 5070 Ti", 1)):
        tasks = runner.build_tasks({**cfg, "prodotti": [settings.clean_product({"id": "r", "nome": name})]})[0]
        assert sum(x.source == "aliexpress" for x in tasks) == n, name


def test_kit_scritto_con_i_moduli_dopo():
    assert 32 in values_in_title("Lexar THOR DDR5 6000MHz 16GBx2 CL30", "GB")
    assert 32 in values_in_title("Netac DDR5 (16Gx2) 6000MHz", "GB")
    assert 32 in values_in_title("G.Skill DDR5 32 GB (16X2)", "GB")
    assert _ram("Lexar THOR DDR5 6000MHz 16GBx2 CL30 1.35V").ok
    assert not _ram("Lexar THOR DDR5 6000MHz 8GBx2 CL30").ok


def test_inserzioni_con_piu_varianti():
    assert _ram("Lancer Blade DDR5 32GB 4800/5600/6000/6400MHz CL30").variants
    for title in ("KingBank RAM DDR5 per Desktop 16GB/32GB 6000MHz CL30", "Netac DDR5 32GB (16Gx2) 4800MHz 5600MHz 6000MHz CL30", "KingSpec DDR5 32GB 5600MHz 6400MHz 6000MHz CL30"):
        d = _ram(title)
        assert d.ok and d.variants and any("varianti" in w for w in d.warnings), title
    for title in ("Corsair DDR5 32GB (2x16GB) 6000MHz CL30", "G.Skill DDR5 2x16GB 32GB 6000 MHz CL30", "Patriot 32 GB 2 x 16 GB DDR5 6000 MHz CL30"):
        assert not _ram(title).variants, title
    cfg = {**CFG, "prodotti": [product()]}
    assert quality.picks([{**_offer(300), "extra": {"varianti": True}}, _offer(500)], cfg)["p"]["total"] == 500


class _EbayReply:
    def __init__(self, status, data):
        self.status_code, self._data = status, data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ebay.requests.HTTPError(response=self)

    def json(self):
        return self._data


EBAY_CFG = {**settings.defaults(), "generale": {**settings.defaults()["generale"], "valuta": "EUR", "paese": "IT"}, "siti": {"attivi": [], "personalizzati": []},
            "telegram": {"canali": []}, "prodotti": [settings.clean_product({"id": "p", "nome": "RTX 5070 Ti"})], "ebay": {"app_id": "A", "cert_id": "SEGRETO"}}


def test_ebay_senza_chiave_nessuna_richiesta():
    cfg = {**EBAY_CFG, "ebay": {"app_id": "", "cert_id": ""}}
    assert runner.build_tasks(cfg)[0] == []
    tasks = runner.build_tasks(EBAY_CFG)[0]
    assert [(x.source, x.kind, x.market) for x in tasks] == [("ebay_api", "ebay", "EBAY_IT")]


def test_ebay_legge_le_offerte():
    calls = []

    def post(url, **kw):
        assert kw["auth"] == ("A", "SEGRETO")
        calls.append("token")
        return _EbayReply(200, {"access_token": "T", "expires_in": 7200})

    def get(url, **kw):
        calls.append(kw["headers"]["X-EBAY-C-MARKETPLACE-ID"])
        assert kw["headers"]["Authorization"] == "Bearer T" and "NEW" in kw["params"]["filter"]
        return _EbayReply(200, {"itemSummaries": [
            {"title": "MSI RTX 5070 Ti Ventus", "price": {"value": "1200.00", "currency": "EUR"}, "itemWebUrl": "https://ebay.it/itm/1", "seller": {"username": "shop"},
             "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "EUR"}}]},
            {"title": "Asus RTX 5070 Ti", "price": {"value": "1000.00", "currency": "GBP"}, "itemWebUrl": "https://ebay.it/itm/2"},
            {"title": "Senza prezzo", "itemWebUrl": "https://ebay.it/itm/3"}]})

    orig = ebay.requests.post, ebay.requests.get
    ebay._tokens.clear()
    ebay.requests.post, ebay.requests.get = post, get
    try:
        res = runner.run_task(None, runner.build_tasks(EBAY_CFG)[0][0], EBAY_CFG)
        runner.run_task(None, runner.build_tasks(EBAY_CFG)[0][0], EBAY_CFG)
    finally:
        ebay.requests.post, ebay.requests.get = orig
    assert calls.count("token") == 1, "the token is reused"
    assert len(res.items) == 2 and res.items[0].shipping == 10.0 and res.items[0].shop == "eBay IT" and res.items[0].currency == "EUR"
    assert res.items[1].currency == "GBP" and res.pages[0].ok
    cfg = {**CFG, "prodotti": [product()]}
    offers, _ = runner.classify_results(cfg, Rules(cfg), [res], TABLE)
    assert {o["total"] for o in offers} == {1210.0, 1250.0}, "the pound is converted"


def test_ebay_errori_senza_segreti():
    def post(url, **kw):
        return _EbayReply(401, {"error": "invalid_client"})

    orig = ebay.requests.post
    ebay._tokens.clear()
    ebay.requests.post = post
    try:
        page, items = ebay.search(EBAY_CFG, "x", "EBAY_IT")
    finally:
        ebay.requests.post = orig
    assert not page.ok and items == [] and "chiave rifiutata" in page.error and "SEGRETO" not in page.error


def test_ebay_salvato_senza_toccare_il_resto():
    cfg = settings.defaults()
    settings.apply_update(cfg, {"ebay": {"app_id": " A ", "cert_id": " B "}})
    assert cfg["ebay"] == {"app_id": "A", "cert_id": "B"}
    settings.apply_update(cfg, {"ebay": {"app_id": "C"}})
    assert cfg["ebay"] == {"app_id": "C", "cert_id": "B"}


def test_pagina_di_accesso_e_un_blocco():
    assert looks_blocked(200, "<html>x</html>", "https://passport.jd.com/new/login.aspx?x=1")
    assert looks_blocked(200, "x", "https://www.temu.com/login.html?from=a")
    assert looks_blocked(200, "x", "https://shopee.sg/verify/traffic/error")
    assert not looks_blocked(200, "x", "https://www.amazon.it/s?k=login")


def test_prezzo_thailandese():
    assert [p[0] for p in extract.prices_in("19,900.-", "THB")] == [19900.0]


# ------------------------------------------------------------------ choice and report
def _offer(total, level="esatto", shop="S", warnings=(), url=None):
    return {"component": "p", "model": "M", "level": level, "title": f"RTX 5070 Ti {total}", "price": total, "shipping": None,
            "total": total, "shop": shop, "source": "f", "url": url or f"https://x/{total}?a=1&b=2", "warnings": list(warnings), "tags": []}


def _store(offers):
    store = Store(":memory:")
    run_id = store.new_run()
    store.add_offers(run_id, offers)
    store.finish_run(run_id, {"f": {"richieste": 1, "ok": 1, "bloccate": 0, "errori": 0, "saltate": 0, "trovati": 1, "validi": 1, "metodi": "x", "ultimo_errore": ""}})
    return store


def test_esatto_batte_simile_ma_il_simile_resta_visibile():
    cfg = {**CFG, "prodotti": [product()]}
    assert quality.picks([_offer(800, "simile"), _offer(1000)], cfg)["p"]["total"] == 1000
    txt = report.telegram_summary(cfg, _store([_offer(800, "simile"), _offer(1000)]))
    assert "1.000,00 €" in txt and "Più basso ma da verificare" in txt and "800,00 €" in txt and "Simile" in txt


def test_se_non_c_e_l_esatto_si_propone_il_simile_e_lo_dice():
    cfg = {**CFG, "prodotti": [product()]}
    txt = report.telegram_summary(cfg, _store([_offer(800, "simile", warnings=["manca Ti"])]))
    assert "800,00 €</b> · Simile" in txt and "⚠ manca Ti" in txt


def test_negozio_dubbio_e_prezzo_anomalo():
    cfg = {**CFG, "prodotti": [product()]}
    assert quality.picks([_offer(300, shop="AliExpress"), _offer(320)], cfg)["p"]["total"] == 320
    offers = [_offer(t) for t in (185, 480, 500, 520)]
    assert quality.picks(offers, cfg)["p"]["total"] == 480
    quality.assess(offers, cfg)
    assert sum("anomalo" in w for w in offers[0]["warnings"]) == 1


def test_report_valuta_e_lingua():
    cfg = {"generale": {"lingua": "en", "valuta": "USD", "paese": "US"}, "prodotti": [product()]}
    path = Path(os.environ["PW_DATA"]) / "r.html"
    page = Path(report.generate(cfg, _store([_offer(1299.5)]), str(path))).read_text(encoding="utf-8")
    assert "$1,299.50" in page and "Exact" in page and 'lang="en"' in page


def test_titolo_e_link_codificati():
    cfg = {**CFG, "prodotti": [product()]}
    o = _offer(500)
    o["title"] = "A & B <kit>"
    txt = report.telegram_summary(cfg, _store([o]))
    assert "A &amp; B &lt;kit&gt;" in txt and "a=1&amp;b=2" in txt


def test_giro_vuoto_non_sostituisce_l_ultimo_e_prune():
    store = _store([_offer(500)])
    good = store.last_run()["id"]
    empty = store.new_run()
    store.finish_run(empty, {})
    assert store.last_run()["id"] == good
    store.add_best(good, {"p": 500})
    store.db.execute("UPDATE offers SET ts='2020-01-01T00:00:00'")
    store.prune()
    assert store.offers_of_run(good) == [] and store.min_before("p", 99) == 500


# ------------------------------------------------------------------ configuration and schedules
def test_controlli_prodotto():
    for bad in ({"nome": " "}, {"nome": "x", "prezzo_min": 10, "prezzo_max": 5}, {"nome": "x", "prezzo_max": "tanto"},
                {"nome": "x", "specifiche": [{"op": "min", "valore": "molti"}]}, {"nome": "x", "pagine": ["ftp://a"]}):
        try:
            settings.clean_product(bad)
        except ValueError:
            continue
        raise AssertionError(bad)
    p = settings.clean_product({"nome": "x y", "specifiche": [{"valore": ""}], "alternative": [{"testo": ""}]})
    assert p["ricerca"] == ["x y"] and p["specifiche"] == [] and p["alternative"] == [] and p["id"]


def test_canali_e_siti_aggiunti():
    for text in ("@prezzone", "https://t.me/prezzone", "t.me/s/prezzone?q=x", "prezzone"):
        assert settings.clean_channel(text) == "prezzone"
    try:
        settings.clean_channel("https://evil.com/<x>")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid channel accepted")
    g = settings.defaults()["generale"]
    site = settings.clean_custom_site({"url": "https://shop.example/s?q={q}"}, g)
    assert site["nome"] == "shop.example" and site["id"].startswith("custom_")
    try:
        settings.clean_custom_site({"url": "https://shop.example/s"}, g)
    except ValueError:
        return
    raise AssertionError("indirizzo senza {q} accettato")


def test_salvataggio_e_riletto():
    cfg = settings.load()
    settings.save(settings.apply_update(cfg, {"prodotti": [{"nome": "Prodotto è"}], "generale": {"intervallo_ore": 6, "paese": "IT"}, "telegram": {"canali": ["@prezzone", "prezzone"]}}))
    again = settings.load()
    assert again["prodotti"][0]["nome"] == "Prodotto è" and again["generale"]["intervallo_ore"] == 6 and again["telegram"]["canali"] == ["prezzone"]
    try:
        settings.apply_update(again, {"generale": {"intervallo_ore": 0}})
    except ValueError:
        return
    raise AssertionError("intervallo 0 accettato")


def test_orari():
    from datetime import datetime
    assert schedule.hours_of_day(3) == [0, 3, 6, 9, 12, 15, 18, 21] and schedule.hours_of_day(24) == [0]
    assert schedule.next_run(3, datetime(2026, 1, 1, 10, 30)) == datetime(2026, 1, 1, 12, 0)
    assert schedule.next_run(3, datetime(2026, 1, 1, 22, 0)) == datetime(2026, 1, 2, 0, 0)
    line = schedule.cron_line(6)
    assert line.startswith("0 0,6,12,18 * * * ") and schedule.CRON_MARK in line


def test_catalogo_coerente():
    ids = [s["id"] for s in catalog.SITES]
    assert len(ids) == len(set(ids)), "id doppi"
    for s in catalog.SITES:
        assert "{q}" in s["url"] and s["paese"] in catalog.COUNTRIES and s["valuta"] in extract.CURRENCY_TOKENS, s["id"]


def test_token_non_finisce_nel_log():
    def post(url, **kw):
        raise OSError(url)
    orig, creds = notify.requests.post, notify._creds
    notify.requests.post, notify._creds = post, lambda cfg: ("SEGRETO", "c")
    try:
        assert "SEGRETO" not in notify.send(CFG, "x")
    finally:
        notify.requests.post, notify._creds = orig, creds


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("ok", name)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print("FALLITO", name, type(e).__name__, str(e)[:200])
    print("falliti:", failed)
    sys.exit(1 if failed else 0)
