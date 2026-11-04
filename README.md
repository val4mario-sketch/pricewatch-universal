# PriceWatch Universale

Tiene d'occhio i prezzi dei prodotti che scegli, su siti e canali Telegram che scegli, e ti avvisa. Se non trova il modello
esatto, propone quello simile o superiore e lo segnala. Gira sul tuo computer: non servono account né server.

Serve Python 3.10 o più recente.

- **Windows:** doppio clic su `Avvia PriceWatch.bat`
- **macOS e Linux:** `sh avvia.sh`

La prima volta installa da solo le librerie. Poi si apre la pagina nel browser, con quattro sezioni.

| Sezione | Cosa fai |
|---|---|
| Prodotti | Con **+** aggiungi un prodotto; nella sua finestra imposti specifiche, margini, prezzi e modelli alternativi |
| Siti e canali | Attivi o togli siti, ne aggiungi di tuoi, aggiungi canali Telegram pubblici, provi se funzionano |
| Esecuzione | Scegli ogni quante ore far girare il controllo, lo attivi, fai un giro subito |
| Risultati | Vedi tutte le offerte, dalla più bassa; in cima a ogni prodotto c'è la più affidabile |

In **Impostazioni** scegli Paese e valuta e colleghi il bot Telegram. L'app parte in inglese: la lingua (English o Italiano) si
cambia dal menu in basso a sinistra, e vale anche per report e messaggi Telegram.

## Dal telefono

L'app e la sua pagina girano solo sul computer, e non si aprono dal telefono. Sul telefono arrivano i risultati, tramite Telegram:

1. Sul computer, in **Impostazioni**, collega il bot seguendo i tre passi indicati e premi **Invia una prova**.
2. In **Esecuzione** attiva l'avvio automatico.
3. A ogni giro ricevi su Telegram l'offerta più affidabile di ogni prodotto con il link, il prezzo più basso se è un altro, gli
   avvisi di prezzo e il file `report.html`. Apri il file da Telegram per vedere l'elenco completo.

Il computer deve essere acceso all'ora del giro. Dal telefono non si aggiungono prodotti né si cambiano le impostazioni.

## Come giudica un'offerta

| Esito | Quando |
|---|---|
| Esatto | Nel titolo ci sono tutte le parole del nome e le specifiche sono rispettate |
| Superiore | Una specifica è migliore della richiesta, o il modello è tra le alternative "superiori" |
| Simile | Una specifica è dentro il margine, il modello è tra le alternative "simili", o manca una sola parola del nome (nomi di almeno 3 parole, mai la prima né un numero di modello) |
| Scartata | Specifica oltre il margine, prezzo fuori dai limiti, usato, ricondizionato o accessorio |

I valori scritti nel nome contano come specifiche: con "32 GB ram ddr5 6000 CL30" il prodotto è la DDR5, con almeno 32 GB (anche se
scritti 2x16GB), almeno 6000 MHz (anche 6000 MT/s) e al massimo CL30. CL28 o 6400 MHz risultano superiori. Parole generiche come
"ram", "memoria" o "kit" non servono a riconoscerlo. Con le DDR si scartano anche SO-DIMM, ECC e schede madri.

I prezzi sotto il 15% della mediana delle offerte di quel prodotto sono numeri letti male e non compaiono. Quelli sotto il 60% del
quartile basso restano visibili con l'avviso di prezzo anomalo. Se un'offerta mostra più numeri, quelli sotto un quarto del più alto
(prezzo al GB, rate) non contano come prezzo.

Una specifica che il titolo non indica non scarta l'offerta: resta un avviso da verificare. Usato, ricondizionato, accessori e
computer interi sono riconosciuti in molte lingue, anche cinese, giapponese e coreano. Un elenco di parole non è perfetto: se passa
qualcosa di sbagliato, aggiungi la parola tra quelle da escludere del prodotto.

## Punteggio, offerte incerte e scartate

Ogni titolo riceve un punteggio di somiglianza, come in un motore di ricerca: i numeri di modello pesano tre volte le altre parole e
una parola scritta quasi uguale conta. Un'offerta che non corrisponde del tutto ma non sbaglia il numero di modello e arriva almeno al
60% resta visibile come **Incerto**, in fondo all'elenco: viene scelta solo se non c'è altro. Le offerte scartate non spariscono: in
fondo a ogni prodotto del report c'è l'elenco col motivo, dalle più vicine a ciò che cerchi.

Quando nel titolo c'è il codice del produttore, lo stesso prodotto viene riconosciuto in tutti i negozi: il report dice quante offerte
ha quel modello e da quale prezzo, e un prezzo è anomalo rispetto allo stesso modello invece che a tutta la categoria.

## IA locale

Se sul computer c'è [Ollama](https://ollama.com) con un modello, PriceWatch lo usa per le offerte dubbie. Si attiva e si spegne in
**Impostazioni**. Nulla esce dal computer e, se Ollama non è attivo, il giro continua con le sole regole.

Un modello piccolo sbaglia, quindi fa solo ciò in cui è stato misurato affidabile (`python tools/prova_ia.py`):

- legge valori che le regole non capiscono. Un numero che non compare davvero nel titolo viene ignorato;
- riconosce accessori e computer interi. Un'offerta incerta viene tolta e finisce tra le scartate; un'offerta che le regole
  considerano buona resta visibile, segnata come dubbia e con affidabilità bassa.

Non decide se il modello è quello giusto (nelle prove confondeva RTX 5070 e 5070 Ti) e non decide i prezzi: restano alle regole. Su un
portatile senza scheda video servono circa 5 secondi a offerta, quindi controlla al massimo 40 offerte per prodotto e si ferma dopo 5
minuti, partendo da quelle dei negozi del tuo Paese. I titoli già visti non si ricontrollano.

## Grado di affidabilità

Ogni offerta, nel report e su Telegram, ha un grado. L'esito sopra dice se è il prodotto giusto, il grado dice quanto fidarsi
di prezzo e prodotto.

| Grado | Quando |
|---|---|
| Alta | Nessun punto di rischio |
| Media | Da 1 a 3 punti |
| Bassa | 4 punti o più, oppure prezzo anomalo o negozio da verificare |

Un punto ciascuno: negozio estero, prezzo convertito, sito letto col browser, sito letto in modo approssimativo, ogni specifica
non indicata nel titolo. Due punti: segnalazione da un canale Telegram.

L'offerta scelta è la meno cara tra quelle senza dubbi su negozio e prezzo, esatte o superiori, senza dogana e con le specifiche lette.
Un negozio di un altro Paese dell'UE compete quindi col prezzo: resta l'avviso di verificare la spedizione. Se manca, si passa alle
simili, poi ai negozi fuori dall'UE, dove dogana e commissioni non sono nel prezzo. Il grado di affidabilità resta scritto accanto. Il prezzo più basso, se è un altro, resta visibile con il motivo per cui va verificato.

## Siti

Il catalogo copre tutto il mondo, compresi negozi internazionali e cinesi come AliExpress. Al primo avvio sono attivi tutti i siti
che hanno funzionato alla prova, di qualsiasi Paese: il Paese che scegli decide solo quali compaiono per primi e quali sono "esteri".
Ogni sito si può spegnere, togliere con la **×** (e ripristinare) o aggiungere: incolli l'indirizzo di una ricerca e indichi Paese e
valuta del sito.

AliExpress parte tra i "negozi da considerare dubbi": le sue offerte si vedono ma viene scelta solo se non c'è altro. Puoi cambiarlo
in **Impostazioni**.

Per RAM e SSD, quando cerchi la categoria e non un marchio, su AliExpress si cercano anche i marchi cinesi: KingBank, Gloway, Netac,
KingSpec, Lexar e Fanxiang. I siti dei produttori quasi non mostrano prezzi. Molte inserzioni elencano più varianti ("16GB/32GB"): il
prezzo è spesso quello della più economica, quindi restano visibili ma segnate come dubbie e non vengono scelte.

I negozi noti che bloccano la ricerca automatica si raggiungono in altri modi. Da Trovaprezzi, che resta attivo di default, arrivano
le offerte di eBay, Unieuro, MediaWorld, Amazon, Kaufland, BPM Power e altri, col nome del negozio e il link: PriceWatch apre fino a 5
schede di prodotto per ricerca. Di Euronics si leggono le pagine prodotto: incolla il link in "Pagine da controllare direttamente" nella
finestra del prodotto. ePrice per ora non è raggiungibile.

Per eBay la via giusta è l'interfaccia ufficiale: crea una chiave gratuita "Production" su developer.ebay.com e inserisci App ID e
Cert ID in **Impostazioni**. Da quel momento eBay del tuo Paese entra da solo in ogni giro, solo oggetti nuovi a prezzo fisso, senza
bisogno di Chrome. Per gli altri negozi che bloccano, **Risultati** ha i pulsanti che aprono la ricerca nel tuo browser: lì guardi tu,
perché l'app non pilota il browser per aggirare i blocchi.

I siti costruiti in JavaScript si aprono con un browser invisibile (Chromium, circa 150 MB, scaricato al primo avvio). Non si apre
nessuna finestra: le loro offerte finiscono nello stesso giro, nello stesso report e nello stesso messaggio Telegram degli altri siti.
Una pagina che non risponde viene chiusa e il giro prosegue. Alcuni siti chiedono comunque l'accesso o una verifica anti-bot (JD, Temu,
Shopee, Lazada) o non mostrano offerte senza accesso (Taobao, Tmall): PriceWatch non entra negli account e non aggira queste verifiche.

Nel catalogo ogni sito mostra l'esito dell'ultima prova. "Bloccato" vuol dire che il sito rifiuta le richieste automatiche:
PriceWatch non prova ad aggirare captcha o sistemi anti-bot. Può dipendere anche dal Paese da cui ti colleghi, quindi prova il
sito col pulsante **Prova**: lo stesso sito può funzionare da un'altra rete.

I prezzi in un'altra valuta vengono convertiti nella tua col cambio della Banca Centrale Europea, scaricato al massimo una volta ogni 12 ore. L'offerta mostra il prezzo originale e la
data del cambio. Il prezzo convertito è indicativo: dogana, commissioni della carta e spedizione verso il tuo Paese non sono
incluse, quindi a parità di condizioni viene preferito un negozio senza questi avvisi.

Senza rete si usa l'ultimo cambio salvato, fino a 14 giorni. Oltre, i siti in un'altra valuta vengono saltati e il report lo dice.
I canali Telegram si leggono nella tua valuta. Le pagine dirette si convertono solo se dichiarano la propria valuta nei dati della
pagina.

Le pause tra le richieste allo stesso sito (3–6 s) sono volute. Se un sito blocca o dà errore due volte di fila, si ferma fino
al giro successivo.

## File

Tutto ciò che è tuo sta in `dati/`: `config.yaml` (con il token Telegram, da non condividere), storico, cambi, report e registro.
Per passare l'app a qualcuno, escludi quella cartella.

Per riprovare tutto il catalogo:

    python tools/prova_catalogo.py

Per i test:

    python tests/test_universal.py
