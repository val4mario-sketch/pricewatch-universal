# PriceWatch Universal

Keeps an eye on the prices of the products you choose, on the sites and Telegram channels you choose, and alerts you. If it cannot
find the exact model, it suggests a similar or better one and says so. It runs on your computer: no accounts or servers needed.

Requires Python 3.10 or later.

- **Windows:** double-click `Avvia PriceWatch.bat`
- **macOS and Linux:** `sh avvia.sh`

The first time, it installs the libraries by itself. Then a page opens in your browser, with four sections.

| Section | What you do |
|---|---|
| Products | Add a product with **+**; in its window you set specifications, margins, prices and alternative models |
| Sites & channels | Turn sites on or off, add your own, add public Telegram channels, test whether they work |
| Schedule | Choose how many hours between checks, turn it on, run a check right away |
| Results | See all the offers, from the lowest; the most reliable one is at the top of each product |

In **Settings** you choose your country and currency and connect the Telegram bot. The app starts in English: the language (English or
Italiano) can be changed from the menu at the bottom left, and it also applies to reports and Telegram messages.

## From your phone

The app and its page run only on the computer and cannot be opened from a phone. Your phone receives the results through Telegram:

1. On the computer, in **Settings**, connect the bot by following the three steps shown and press **Send a test**.
2. In **Schedule**, turn on automatic runs.
3. At each run you receive on Telegram the most reliable offer for each product with its link, the lowest price if that is a different
   offer, price alerts and the `report.html` file. Open the file from Telegram to see the full list.

The computer must be on at the time of the run. You cannot add products or change settings from the phone.

## How it judges an offer

| Result | When |
|---|---|
| Exact | The title contains all the words in the name and the specifications are met |
| Better | A specification is better than requested, or the model is among the "better" alternatives |
| Similar | A specification is within the margin, the model is among the "similar" alternatives, or a single word of the name is missing (names of at least 3 words, never the first word or a model number) |
| Discarded | Specification beyond the margin, price outside the limits, used, refurbished or an accessory |

Values written in the name count as specifications: with "32 GB ram ddr5 6000 CL30" the product is DDR5, with at least 32 GB (even if
written 2x16GB), at least 6000 MHz (also 6000 MT/s) and at most CL30. CL28 or 6400 MHz count as better. Generic words such as "ram",
"memory" or "kit" are not used to recognize it. For DDR memory, SO-DIMM, ECC and motherboards are also discarded.

Prices below 15% of the median of a product's offers are misread numbers and do not appear. Those below 60% of the lower quartile stay
visible with an unusual-price warning. If an offer shows several numbers, those below a quarter of the highest (price per GB,
instalments) do not count as the price.

A specification the title does not state does not discard the offer: it stays as a warning to check. Used, refurbished, accessories and
whole computers are recognized in many languages, including Chinese, Japanese and Korean. A word list is not perfect: if something wrong
gets through, add the word to the product's words to exclude.

## Score, uncertain and discarded offers

Each title gets a similarity score, as in a search engine: model numbers weigh three times as much as other words, and a nearly
identical word counts. An offer that does not fully match but does not get the model number wrong and reaches at least 60% stays visible
as **Uncertain**, at the bottom of the list: it is chosen only if there is nothing else. Discarded offers do not disappear: at the bottom
of each product in the report is the list with the reason, starting from those closest to what you are looking for.

When the title contains the manufacturer's code, the same product is recognized in all shops: the report says how many offers that
model has and from what price, and a price is judged unusual against the same model rather than the whole category.

## Local AI

If [Ollama](https://ollama.com) with a model is on the computer, PriceWatch uses it for doubtful offers. Turn it on or off in
**Settings**. Nothing leaves the computer and, if Ollama is not running, the run continues with the rules alone.

A small model makes mistakes, so it does only what it has been measured to do reliably (`python tools/prova_ia.py`):

- it reads values the rules do not understand. A number that does not actually appear in the title is ignored;
- it recognizes accessories and whole computers. An uncertain offer is removed and goes among the discarded ones; an offer the rules
  consider good stays visible, marked as doubtful and with low reliability.

It does not decide whether the model is the right one (in tests it confused the RTX 5070 and 5070 Ti) and does not decide prices: those
stay with the rules. On a laptop without a graphics card it takes about 5 seconds per offer, so it checks at most 40 offers per product
and stops after 5 minutes, starting with the shops in your country. Titles already seen are not checked again.

## Reliability grade

Each offer, in the report and on Telegram, has a grade. The result above says whether it is the right product; the grade says how far to
trust the price and the product.

| Grade | When |
|---|---|
| High | No risk points |
| Medium | 1 to 3 points |
| Low | 4 points or more, or an unusual price or a shop to verify |

One point each: foreign shop, converted price, site read with the browser, site read approximately, each specification not stated in the
title. Two points: a report from a Telegram channel.

The chosen offer is the cheapest among those with no doubts about shop and price, exact or better, with no customs and with the
specifications read. A shop in another EU country therefore competes on price, with a reminder to check delivery. If there is none, it
moves on to similar offers, then to shops outside the EU, where customs and fees are not included in the price. The reliability grade
stays written next to it. The lowest price, if it is a different offer, stays visible with the reason it needs checking.

## Sites

The catalogue covers the whole world, including international and Chinese shops such as AliExpress. On first launch, all the sites that
worked when tested are on, from any country: the country you choose only decides which appear first and which count as foreign. Each
site can be turned off, removed with the **×** (and restored) or added: paste the address of a search and state the site's country and
currency.

AliExpress starts among the shops to treat as doubtful: its offers are visible but one is chosen only if there is nothing else. You can
change this in **Settings**.

For RAM and SSDs, when you search for the category and not a brand, AliExpress is also searched for Chinese brands: KingBank, Gloway,
Netac, KingSpec, Lexar and Fanxiang. Manufacturers' sites hardly show any prices. Many listings show several variants ("16GB/32GB"): the
price is often that of the cheapest, so they stay visible but are marked as doubtful and are not chosen.

Well-known shops that block automated searches are reached in other ways. Trovaprezzi, which stays on by default, supplies offers from
eBay, Unieuro, MediaWorld, Amazon, Kaufland, BPM Power and others, with the shop name and link: PriceWatch opens up to 5 product pages per
search. For Euronics, product pages are read: paste the link in "Pages to check directly" in the product window. ePrice cannot be reached
for now.

For eBay the right way is the official interface: create a free "Production" key on developer.ebay.com and enter the App ID and Cert ID
in **Settings**. From then on, eBay in your country joins every run by itself, new fixed-price items only, with no need for Chrome. For
other shops that block automated access, **Results** has buttons that open the search in your browser: you look there yourself, because
the app does not drive the browser to get around blocks.

Sites built in JavaScript are opened with an invisible browser (Chromium, about 150 MB, downloaded on first launch). No window opens:
their offers end up in the same run, report and Telegram message as the other sites. A page that does not respond is closed and the run
continues. Some sites still ask for a login or an anti-bot check (JD, Temu, Shopee, Lazada) or show no offers without a login (Taobao,
Tmall): PriceWatch does not log in to accounts or get around these checks.

In the catalogue, each site shows the outcome of its last test. "Blocked" means the site refuses automated requests: PriceWatch does not
try to get around captchas or anti-bot systems. It can also depend on the country you connect from, so test the site with the **Test**
button: the same site may work from another network.

Prices in another currency are converted into yours at the European Central Bank rate, downloaded at most once every 12 hours. The offer
shows the original price and the rate date. The converted price is indicative: customs, card fees and shipping to your country are not
included, so, other things being equal, a shop without these warnings is preferred.

Offline, the last saved rate is used, for up to 14 days. After that, sites in another currency are skipped and the report says so.
Telegram channels are read in your currency. Direct pages are converted only if they declare their currency in the page data.

The pauses between requests to the same site (3–6 s) are intentional. If a site blocks or gives an error twice in a row, it stops until
the next run.

## Files

Everything of yours is in `dati/`: `config.yaml` (with the Telegram token, not to be shared), history, exchange rates, reports and the
log. To pass the app to someone, leave that folder out.

To test the whole catalogue again:

    python tools/prova_catalogo.py

To run the tests:

    python tests/test_universal.py
