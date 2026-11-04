"""Siti pronti all'uso. {q} è il termine cercato. Gli esiti delle prove reali stanno in catalog_status.json."""
from __future__ import annotations

import json
import re
from pathlib import Path

_AMAZON = {"item": "div[data-component-type='s-search-result']", "titolo": "h2", "prezzo": ".a-price .a-offscreen",
           "link": "a.a-link-normal[href*='/dp/'], h2 a"}
_EBAY = {"item": "li.s-item, li.s-card", "titolo": ".s-item__title, .s-card__title", "prezzo": ".s-item__price, .s-card__price",
         "spedizione": ".s-item__shipping, .s-item__logisticsCost", "link": "a[href*='/itm/']"}
_IDEALO = {"item": "[class*='sr-resultList__item']", "titolo": "[class*='productSummary__title']",
           "prezzo": "[class*='detailedPriceInfo__price']"}
_GEIZHALS = {"item": "article.listview__item, div.productlist__product, div.galleryview__item",
             "titolo": ".listview__name-link, .productlist__name a, .galleryview__name-link",
             "prezzo": ".listview__price, .productlist__price, .gh_price, .price"}


def _amazon(tld, country, cur):
    return {"id": f"amazon_{country.lower()}", "nome": f"Amazon.{tld}", "paese": country, "valuta": cur, "tipo": "negozio",
            "url": f"https://www.amazon.{tld}/s?k={{q}}", "negozio": f"Amazon.{tld}", "selettori": _AMAZON}


def _ebay(tld, country, cur):
    return {"id": f"ebay_{country.lower()}", "nome": f"eBay.{tld}", "paese": country, "valuta": cur, "tipo": "negozio",
            "url": f"https://www.ebay.{tld}/sch/i.html?_nkw={{q}}&LH_ItemCondition=1000&LH_BIN=1&_sop=15",
            "negozio": f"eBay.{tld}", "selettori": _EBAY}


def _site(sid, name, country, cur, url, tipo="negozio", selectors=None, shop=None, espandi=""):
    # espandi: i risultati raggruppati del comparatore, da aprire per vedere le offerte dei singoli negozi
    return {"id": sid, "nome": name, "paese": country, "valuta": cur, "tipo": tipo, "url": url,
            "negozio": "" if tipo == "comparatore" else (shop or name), "selettori": selectors, "espandi": espandi}


def _global(sid, name, url, selectors=None):
    """Negozio internazionale: mostra i prezzi nella valuta di chi visita, quindi nella tua."""
    return {**_site(sid, name, "WW", "USD", url, selectors=selectors), "valuta_visitatore": True}


SITES = [
    # Italia
    _site("trovaprezzi", "Trovaprezzi", "IT", "EUR", "https://www.trovaprezzi.it/categoria.aspx?libera={q}&id=-1&prezzomin=&prezzomax=",
          "comparatore", {"item": "li.listing_item, div.listing_item", "titolo": ".item_name, a.item_name",
                          "prezzo": ".item_basic_price, .item_price", "spedizione": ".item_delivery_price",
                          "negozio": ".merchant_name, .merchant img"}, espandi="a.relevant_item"),
    _site("idealo_it", "Idealo.it", "IT", "EUR", "https://www.idealo.it/risultati.html?q={q}", "comparatore", _IDEALO),
    _amazon("it", "IT", "EUR"), _ebay("it", "IT", "EUR"),
    _site("eprice", "ePrice", "IT", "EUR", "https://www.eprice.it/sa/?qs={q}"),
    _site("unieuro", "Unieuro", "IT", "EUR", "https://www.unieuro.it/online/products?q={q}"),
    _site("mediaworld", "MediaWorld", "IT", "EUR", "https://www.mediaworld.it/it/search.html?query={q}"),
    _site("euronics_it", "Euronics", "IT", "EUR", "https://www.euronics.it/search?q={q}"),
    _site("akinformatica", "AK Informatica", "IT", "EUR", "https://www.akinformatica.it/ricerca?controller=search&s={q}"),
    _site("pccomponentes_it", "PcComponentes.it", "IT", "EUR", "https://www.pccomponentes.it/search/?query={q}"),
    _site("yeppon", "Yeppon", "IT", "EUR", "https://www.yeppon.it/search/?q={q}"),
    _site("bpm", "BPM Power", "IT", "EUR", "https://www.bpm-power.com/it/ricerca?k={q}"),
    _site("expert_it", "Expert", "IT", "EUR", "https://www.expert.it/it/it/exp/shop/search?terms={q}"),
    _site("comet", "Comet", "IT", "EUR", "https://www.comet.it/search?iq={q}"),
    _site("conrad_it", "Conrad.it", "IT", "EUR", "https://www.conrad.it/it/search.html?search={q}"),
    _site("nexths", "Next", "IT", "EUR", "https://www.nexths.it/Products/search?query={q}"),
    # Germania e Austria
    _site("geizhals", "Geizhals", "DE", "EUR", "https://geizhals.eu/?fs={q}&hloc=at&hloc=de&sort=p", "comparatore", _GEIZHALS),
    _site("idealo_de", "Idealo.de", "DE", "EUR", "https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={q}", "comparatore", _IDEALO),
    _amazon("de", "DE", "EUR"), _ebay("de", "DE", "EUR"),
    _site("alternate_de", "Alternate.de", "DE", "EUR", "https://www.alternate.de/listing.xhtml?q={q}", selectors={"item": "a.productBox", "titolo": ".product-name", "prezzo": ".price"}),
    _site("mindfactory", "Mindfactory", "DE", "EUR", "https://www.mindfactory.de/search_result.php?search_query={q}", selectors={"item": "div.pcontent, div.p", "titolo": ".pname", "prezzo": ".pprice"}),
    _site("caseking", "Caseking", "DE", "EUR", "https://www.caseking.de/search?search={q}"),
    _site("cyberport", "Cyberport", "DE", "EUR", "https://www.cyberport.de/tools/search-results.html?q={q}"),
    _site("galaxus_de", "Galaxus.de", "DE", "EUR", "https://www.galaxus.de/search?q={q}"),
    _site("mediamarkt_de", "MediaMarkt.de", "DE", "EUR", "https://www.mediamarkt.de/de/search.html?query={q}"),
    _site("saturn", "Saturn", "DE", "EUR", "https://www.saturn.de/de/search.html?query={q}"),
    _site("conrad_de", "Conrad.de", "DE", "EUR", "https://www.conrad.de/de/search.html?search={q}"),
    _site("kaufland_de", "Kaufland.de", "DE", "EUR", "https://www.kaufland.de/s/?search_value={q}"),
    _site("mediamarkt_at", "MediaMarkt.at", "AT", "EUR", "https://www.mediamarkt.at/de/search.html?query={q}"),
    # Francia
    _site("idealo_fr", "Idealo.fr", "FR", "EUR", "https://www.idealo.fr/prechcat.html?q={q}", "comparatore", _IDEALO),
    _amazon("fr", "FR", "EUR"), _ebay("fr", "FR", "EUR"),
    _site("ldlc_fr", "LDLC", "FR", "EUR", "https://www.ldlc.com/recherche/{q}/"),
    _site("materiel", "Materiel.net", "FR", "EUR", "https://www.materiel.net/recherche/{q}/"),
    _site("topachat", "TopAchat", "FR", "EUR", "https://www.topachat.com/pages/recherche.php?cat=accueil&etou=0&mc={q}"),
    _site("rueducommerce", "Rue du Commerce", "FR", "EUR", "https://www.rueducommerce.fr/recherche/{q}"),
    _site("cdiscount", "Cdiscount", "FR", "EUR", "https://www.cdiscount.com/search/10/{q}.html"),
    _site("boulanger", "Boulanger", "FR", "EUR", "https://www.boulanger.com/resultats?tr={q}"),
    _site("carrefour_fr", "Carrefour", "FR", "EUR", "https://www.carrefour.fr/s?q={q}"),
    _site("fnac", "Fnac", "FR", "EUR", "https://www.fnac.com/SearchResult/ResultList.aspx?Search={q}"),
    _site("darty", "Darty", "FR", "EUR", "https://www.darty.com/nav/recherche?text={q}"),
    # Spagna e Portogallo
    _site("idealo_es", "Idealo.es", "ES", "EUR", "https://www.idealo.es/resultados.html?q={q}", "comparatore", _IDEALO),
    _amazon("es", "ES", "EUR"), _ebay("es", "ES", "EUR"),
    _site("pccomponentes_es", "PcComponentes", "ES", "EUR", "https://www.pccomponentes.com/search/?query={q}"),
    _site("coolmod", "Coolmod", "ES", "EUR", "https://www.coolmod.com/#!/search/{q}"),
    _site("mediamarkt_es", "MediaMarkt.es", "ES", "EUR", "https://www.mediamarkt.es/es/search.html?query={q}"),
    _site("worten_pt", "Worten", "PT", "EUR", "https://www.worten.pt/search?query={q}"),
    _site("kuantokusta", "KuantoKusta", "PT", "EUR", "https://www.kuantokusta.pt/search?q={q}", "comparatore"),
    _site("globaldata", "Globaldata", "PT", "EUR", "https://www.globaldata.pt/catalogsearch/result/?q={q}"),
    # Paesi Bassi e Belgio
    _amazon("nl", "NL", "EUR"),
    _site("tweakers", "Tweakers Pricewatch", "NL", "EUR", "https://tweakers.net/zoeken/?keyword={q}", "comparatore"),
    _site("coolblue_nl", "Coolblue", "NL", "EUR", "https://www.coolblue.nl/en/search?query={q}"),
    _site("bol", "Bol", "NL", "EUR", "https://www.bol.com/nl/nl/s/?searchtext={q}"),
    _site("megekko", "Megekko", "NL", "EUR", "https://www.megekko.nl/product/{q}"),
    _site("mediamarkt_nl", "MediaMarkt.nl", "NL", "EUR", "https://www.mediamarkt.nl/nl/search.html?query={q}"),
    # Regno Unito e Irlanda
    _site("idealo_uk", "Idealo.co.uk", "GB", "GBP", "https://www.idealo.co.uk/mscat.html?q={q}", "comparatore", _IDEALO),
    _site("pricespy_uk", "PriceSpy", "GB", "GBP", "https://pricespy.co.uk/search?query={q}", "comparatore"),
    _amazon("co.uk", "GB", "GBP"), _ebay("co.uk", "GB", "GBP"),
    _site("scan", "Scan", "GB", "GBP", "https://www.scan.co.uk/search?q={q}"),
    _site("overclockers_uk", "Overclockers UK", "GB", "GBP", "https://www.overclockers.co.uk/search?sSearch={q}"),
    _site("ebuyer", "Ebuyer", "GB", "GBP", "https://www.ebuyer.com/search?q={q}"),
    _site("currys", "Currys", "GB", "GBP", "https://www.currys.co.uk/search?q={q}"),
    _site("argos", "Argos", "GB", "GBP", "https://www.argos.co.uk/search/{q}/"),
    _site("johnlewis", "John Lewis", "GB", "GBP", "https://www.johnlewis.com/search?search-term={q}"),
    _site("very", "Very", "GB", "GBP", "https://www.very.co.uk/e/q/{q}.end"),
    # Svizzera
    _site("toppreise", "Toppreise", "CH", "CHF", "https://www.toppreise.ch/produktsuche?q={q}", "comparatore"),
    _site("galaxus_ch", "Galaxus.ch", "CH", "CHF", "https://www.galaxus.ch/search?q={q}"),
    _site("digitec", "Digitec", "CH", "CHF", "https://www.digitec.ch/search?q={q}"),
    # Paesi nordici
    _site("prisjakt_se", "Prisjakt", "SE", "SEK", "https://www.prisjakt.nu/search?query={q}", "comparatore"),
    _amazon("se", "SE", "SEK"),
    _site("inet", "Inet", "SE", "SEK", "https://www.inet.se/hitta?q={q}"),
    _site("webhallen", "Webhallen", "SE", "SEK", "https://www.webhallen.com/se/search?searchString={q}"),
    _site("prisjakt_no", "Prisjakt.no", "NO", "NOK", "https://www.prisjakt.no/search?query={q}", "comparatore"),
    _site("komplett_no", "Komplett", "NO", "NOK", "https://www.komplett.no/search?q={q}"),
    _site("pricerunner_dk", "PriceRunner.dk", "DK", "DKK", "https://www.pricerunner.dk/results?q={q}", "comparatore"),
    # Europa orientale
    _site("ceneo", "Ceneo", "PL", "PLN", "https://www.ceneo.pl/;szukaj-{q}", "comparatore"),
    _amazon("pl", "PL", "PLN"),
    _site("xkom", "x-kom", "PL", "PLN", "https://www.x-kom.pl/szukaj?q={q}"),
    _site("morele", "Morele", "PL", "PLN", "https://www.morele.net/wyszukiwarka/?q={q}"),
    _site("alza", "Alza", "CZ", "CZK", "https://www.alza.cz/search.htm?exps={q}"),
    _site("heureka", "Heureka", "CZ", "CZK", "https://www.heureka.cz/?h%5Bfraze%5D={q}", "comparatore"),
    # Stati Uniti
    _amazon("com", "US", "USD"), _ebay("com", "US", "USD"),
    _site("newegg", "Newegg", "US", "USD", "https://www.newegg.com/p/pl?d={q}", selectors={"item": "div.item-cell", "titolo": "a.item-title", "prezzo": "li.price-current", "link": "a.item-title"}),
    _site("microcenter", "Micro Center", "US", "USD", "https://www.microcenter.com/search/search_results.aspx?Ntt={q}"),
    _site("bhphoto", "B&H Photo", "US", "USD", "https://www.bhphotovideo.com/c/search?q={q}"),
    _site("bestbuy", "Best Buy", "US", "USD", "https://www.bestbuy.com/site/searchpage.jsp?st={q}"),
    _site("walmart", "Walmart", "US", "USD", "https://www.walmart.com/search?q={q}"),
    _site("target", "Target", "US", "USD", "https://www.target.com/s?searchTerm={q}"),
    _site("slickdeals", "Slickdeals", "US", "USD", "https://slickdeals.net/newsearch.php?q={q}", "comparatore"),
    # Canada
    _amazon("ca", "CA", "CAD"), _ebay("ca", "CA", "CAD"),
    _site("newegg_ca", "Newegg.ca", "CA", "CAD", "https://www.newegg.ca/p/pl?d={q}", selectors={"item": "div.item-cell", "titolo": "a.item-title", "prezzo": "li.price-current", "link": "a.item-title"}),
    _site("canadacomputers", "Canada Computers", "CA", "CAD", "https://www.canadacomputers.com/en/search?s={q}"),
    _site("memoryexpress", "Memory Express", "CA", "CAD", "https://www.memoryexpress.com/Search/Products?Search={q}"),
    # America Latina
    _amazon("com.br", "BR", "BRL"),
    _site("mercadolivre", "Mercado Livre", "BR", "BRL", "https://lista.mercadolivre.com.br/{q}"),
    _site("kabum", "KaBuM!", "BR", "BRL", "https://www.kabum.com.br/busca/{q}"),
    _amazon("com.mx", "MX", "MXN"),
    _site("mercadolibre_mx", "Mercado Libre", "MX", "MXN", "https://listado.mercadolibre.com.mx/{q}"),
    # Asia e Oceania
    _amazon("com.au", "AU", "AUD"), _ebay("com.au", "AU", "AUD"),
    _site("staticice", "StaticICE", "AU", "AUD", "https://www.staticice.com.au/cgi-bin/search.cgi?q={q}", "comparatore"),
    _site("scorptec", "Scorptec", "AU", "AUD", "https://www.scorptec.com.au/search/go?w={q}"),
    _site("pccasegear", "PC Case Gear", "AU", "AUD", "https://www.pccasegear.com/search?query={q}"),
    _site("pricespy_nz", "PriceSpy NZ", "NZ", "NZD", "https://pricespy.co.nz/search?query={q}", "comparatore"),
    _site("pbtech", "PB Tech", "NZ", "NZD", "https://www.pbtech.co.nz/search?sf={q}"),
    _amazon("co.jp", "JP", "JPY"),
    _site("kakaku", "Kakaku", "JP", "JPY", "https://kakaku.com/search_results/{q}/", "comparatore"),
    _amazon("in", "IN", "INR"),
    _site("flipkart", "Flipkart", "IN", "INR", "https://www.flipkart.com/search?q={q}"),
    _site("mdcomputers", "MD Computers", "IN", "INR", "https://mdcomputers.in/index.php?route=product/search&search={q}"),
    _amazon("sg", "SG", "SGD"),
    _amazon("com.tr", "TR", "TRY"),
    _amazon("co.za", "ZA", "ZAR"),
    # Internazionali
    {**_global("aliexpress", "AliExpress", "https://www.aliexpress.com/wholesale?SearchText={q}"), "marchi_cinesi": True},
    _global("temu", "Temu", "https://www.temu.com/search_result.html?search_key={q}"),
    _global("banggood", "Banggood", "https://www.banggood.com/search/{q}.html"),
    _global("dhgate", "DHgate", "https://www.dhgate.com/wholesale/search.do?searchkey={q}"),
    _global("geekbuying", "Geekbuying", "https://www.geekbuying.com/search?keyword={q}"),
    _global("tomtop", "Tomtop", "https://www.tomtop.com/search/{q}.html"),
    _global("joom", "Joom", "https://www.joom.com/en/search/q.{q}", {"item": "a[href*='/products/']", "titolo": "h2", "prezzo": "[class*='pricesRegularValue']"}),
    # Cina e Hong Kong
    _site("juhor", "Juhor", "CN", "USD", "https://juhor.net/?s={q}&post_type=product"),
    _site("biwin", "BIWIN", "CN", "USD", "https://www.biwintech.com/?s={q}&post_type=product"),
    _site("jd", "JD.com", "CN", "CNY", "https://search.jd.com/Search?keyword={q}"),
    _site("taobao", "Taobao", "CN", "CNY", "https://s.taobao.com/search?q={q}"),
    _site("tmall", "Tmall", "CN", "CNY", "https://list.tmall.com/search_product.htm?q={q}"),
    _site("smzdm", "SMZDM", "CN", "CNY", "https://search.smzdm.com/?c=home&s={q}", "comparatore"),
    _site("zol", "ZOL", "CN", "CNY", "https://search.zol.com.cn/s/all.php?kword={q}", "comparatore"),
    _site("pricehk", "Price.com.hk", "HK", "HKD", "https://www.price.com.hk/search.php?g=A&q={q}", "comparatore"),
    # Corea e Giappone
    _site("danawa", "Danawa", "KR", "KRW", "https://search.danawa.com/dsearch.php?query={q}", "comparatore"),
    _site("gmarket", "Gmarket", "KR", "KRW", "https://browse.gmarket.co.kr/search?keyword={q}"),
    _site("coupang", "Coupang", "KR", "KRW", "https://www.coupang.com/np/search?q={q}"),
    _site("rakuten_jp", "Rakuten", "JP", "JPY", "https://search.rakuten.co.jp/search/mall/{q}/"),
    _site("yodobashi", "Yodobashi", "JP", "JPY", "https://www.yodobashi.com/?word={q}"),
    # Sud-est asiatico
    _site("shopee_sg", "Shopee", "SG", "SGD", "https://shopee.sg/search?keyword={q}"),
    _site("lazada_sg", "Lazada", "SG", "SGD", "https://www.lazada.sg/catalog/?q={q}"),
    _site("lazada_my", "Lazada.com.my", "MY", "MYR", "https://www.lazada.com.my/catalog/?q={q}"),
    _site("lazada_th", "Lazada.co.th", "TH", "THB", "https://www.lazada.co.th/catalog/?q={q}"),
    _site("jib", "JIB", "TH", "THB", "https://www.jib.co.th/web/product/product_search/0?str_search={q}"),
    _site("lazada_ph", "Lazada.com.ph", "PH", "PHP", "https://www.lazada.com.ph/catalog/?q={q}"),
    _site("tokopedia", "Tokopedia", "ID", "IDR", "https://www.tokopedia.com/search?q={q}"),
    # Altri Paesi
    _site("zap", "Zap", "IL", "ILS", "https://www.zap.co.il/search.aspx?keyword={q}", "comparatore"),
    _site("skroutz", "Skroutz", "GR", "EUR", "https://www.skroutz.gr/search?keyphrase={q}", "comparatore"),
    _site("emag_ro", "eMAG.ro", "RO", "RON", "https://www.emag.ro/search/{q}"),
    _site("emag_hu", "eMAG.hu", "HU", "HUF", "https://www.emag.hu/search/{q}"),
    _site("arukereso", "Árukereső", "HU", "HUF", "https://www.arukereso.hu/CategorySearch.php?st={q}", "comparatore"),
    _site("pcpartpicker", "PCPartPicker", "US", "USD", "https://pcpartpicker.com/search/?q={q}", "comparatore"),
]

# Pagine costruite in JavaScript: si aprono col browser invisibile, nello stesso giro e nello stesso report degli altri siti.
_WITH_BROWSER = {"amazon_es", "amazon_br", "amazon_mx", "webhallen", "ceneo", "banggood", "joom", "jib", "unieuro", "bpm", "worten_pt"}
SITES = [{**s, "browser": True} if s["id"] in _WITH_BROWSER else s for s in SITES]
# Negozi noti che bloccano la ricerca automatica: la GUI dice come averli comunque.
_NOTES = {"ebay_it": "trovaprezzi", "euronics_it": "pagine", "eprice": "bloccato"}
SITES = [{**s, "nota": _NOTES[s["id"]]} if s["id"] in _NOTES else s for s in SITES]

# Codici ISO: la GUI ne mostra il nome nella lingua scelta. WW sono i negozi internazionali, non un Paese in cui vivere.
COUNTRIES = ["IT", "DE", "AT", "FR", "ES", "PT", "NL", "GB", "CH", "SE", "NO", "DK", "PL", "CZ", "GR", "RO", "HU", "TR", "IL", "US", "CA", "BR", "MX",
             "AU", "NZ", "JP", "CN", "HK", "KR", "IN", "SG", "MY", "TH", "PH", "ID", "ZA", "WW"]
# Marchi cinesi che raramente escono cercando il solo prodotto: sui siti con "marchi_cinesi" si cercano anche per nome.
CHINESE_BRANDS = [(re.compile(r"\bddr\d"), ["KingBank", "Gloway", "Netac", "KingSpec", "Lexar"]),
                  (re.compile(r"\b(?:ssd|nvme)\b"), ["Netac", "KingSpec", "Fanxiang", "Gloway", "Lexar"])]


def brands_for(core_name: str) -> list[str]:
    """Solo per chi cerca una categoria ("ddr5", "ssd"): chi ha scritto un marchio vuole quello."""
    if len(core_name.split()) != 1:
        return []
    return next((brands for rx, brands in CHINESE_BRANDS if rx.search(core_name.lower())), [])


# Tra questi Paesi niente dogana: un negozio tedesco per chi sta in Italia compete col prezzo.
EU_COUNTRIES = {"IT", "DE", "AT", "FR", "ES", "PT", "NL", "SE", "DK", "PL", "CZ", "GR", "RO", "HU"}
CURRENCY_OF = {s["paese"]: s["valuta"] for s in SITES if s["paese"] != "WW"}
ACCEPT_LANGUAGE = {"IT": "it-IT,it;q=0.9,en;q=0.7", "DE": "de-DE,de;q=0.9,en;q=0.7", "FR": "fr-FR,fr;q=0.9,en;q=0.7",
                   "ES": "es-ES,es;q=0.9,en;q=0.7", "PT": "pt-PT,pt;q=0.9,en;q=0.7", "NL": "nl-NL,nl;q=0.9,en;q=0.7",
                   "SE": "sv-SE,sv;q=0.9,en;q=0.7", "NO": "nb-NO,nb;q=0.9,en;q=0.7", "DK": "da-DK,da;q=0.9,en;q=0.7",
                   "PL": "pl-PL,pl;q=0.9,en;q=0.7", "CZ": "cs-CZ,cs;q=0.9,en;q=0.7", "BR": "pt-BR,pt;q=0.9,en;q=0.7",
                   "MX": "es-MX,es;q=0.9,en;q=0.7", "JP": "ja-JP,ja;q=0.9,en;q=0.7", "TR": "tr-TR,tr;q=0.9,en;q=0.7"}
SUGGESTED_CHANNELS = {"IT": ["offertepuntotech", "offertesmartworld", "prezzitech", "mente_informatica", "offertetechoutofbit",
                             "trovapromozioni", "saldisuinternet", "ribassitech", "canaleoffertetecnologia", "offertehardwarepc",
                             "VereOfferteTech", "hardwareByToms", "scontierrati", "prezzone"]}

_STATUS_FILE = Path(__file__).with_name("catalog_status.json")
GATEWAY = "trovaprezzi"  # da qui arrivano eBay e altri negozi noti: resta attivo anche se un giorno limita le richieste


def tested_status() -> dict:
    try:
        return json.loads(_STATUS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def site_list(cfg: dict) -> list[dict]:
    """Catalogo più i siti aggiunti a mano, ognuno con stato di attivazione e ultimo esito di prova."""
    sites_cfg = cfg.get("siti") or {}
    active = set(sites_cfg.get("attivi") or [])
    status = {**tested_status(), **(sites_cfg.get("esiti") or {})}
    removed = set(sites_cfg.get("rimossi") or [])
    out = []
    for s in [*SITES, *(sites_cfg.get("personalizzati") or [])]:
        out.append({**s, "attivo": s["id"] in active and s["id"] not in removed, "rimosso": s["id"] in removed, "personalizzato": s in (sites_cfg.get("personalizzati") or []),
                    "prova": status.get(s["id"])})
    return out


def default_active() -> list[str]:
    """Al primo avvio: tutti i siti del mondo che alla prova hanno restituito offerte, non solo quelli del tuo Paese."""
    status = tested_status()
    return [s["id"] for s in SITES if s["id"] == GATEWAY or (status.get(s["id"]) or {}).get("esito") == "ok"]


def newly_working(seen: list[str]) -> list[str]:
    """I siti funzionanti entrati nel catalogo dopo l'ultimo salvataggio dell'utente."""
    return [x for x in default_active() if x not in seen]


def site_currency(site: dict, home: str) -> str:
    """La valuta in cui il sito scrive i prezzi per chi lo visita."""
    return home if site.get("valuta_visitatore") else site.get("valuta", home)
