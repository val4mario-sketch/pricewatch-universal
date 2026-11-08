'use strict';

const STRINGS = {
  it: {
    'nav.products': 'Prodotti', 'nav.sites': 'Siti e canali', 'nav.auto': 'Esecuzione', 'nav.results': 'Risultati', 'nav.settings': 'Impostazioni',
    'products.title': 'Prodotti', 'products.sub': 'Cosa vuoi tenere d’occhio. Ogni prodotto ha le sue specifiche e i suoi margini.',
    'products.add': 'Aggiungi prodotto', 'products.off': 'In pausa', 'products.max': 'fino a', 'products.alert': 'avviso sotto',
    'products.terms': 'ricerche', 'products.empty': 'Premi + per aggiungere il primo prodotto.',
    'd.new': 'Nuovo prodotto', 'd.edit': 'Modifica prodotto', 'd.name': 'Prodotto cercato', 'd.nameHint': 'Marca e modello, per esempio: RTX 5070 Ti, Sony WH-1000XM5. Valori come 1TB, 32GB o CL30 nel nome valgono come minimo o massimo: un valore migliore è segnalato come superiore.',
    'd.search': 'Termini di ricerca sui siti', 'd.searchHint': 'Premi Invio dopo ogni termine. Se lo lasci vuoto cerca il nome del prodotto. Ogni termine aggiunge una richiesta per ogni sito.',
    'd.specs': 'Specifiche richieste', 'd.specsHint': 'Lette dal titolo dell’offerta. Con il margine, un valore un po’ diverso resta valido e viene segnalato come simile. Oltre il margine l’offerta è scartata.',
    'd.specName': 'Nome', 'd.specOp': 'Condizione', 'd.specValue': 'Valore', 'd.specUnit': 'Unità', 'd.specMargin': 'Margine %', 'd.addSpec': '+ Aggiungi specifica',
    'op.min': 'almeno', 'op.max': 'al massimo', 'op.eq': 'uguale a', 'op.text': 'contiene',
    'd.price': 'Prezzo', 'd.min': 'Minimo', 'd.max': 'Massimo', 'd.alert': 'Avvisami sotto', 'd.priceHint': 'Il minimo scarta accessori e prezzi sbagliati: conviene impostarlo.',
    'd.alts': 'Vanno bene anche', 'd.altsHint': 'Altri modelli che accetteresti. Nel risultato vengono segnalati come simili o superiori.', 'd.altText': 'Modello', 'd.addAlt': '+ Aggiungi modello',
    'level.simile': 'Simile', 'level.superiore': 'Superiore', 'level.esatto': 'Esatto', 'level.incerto': 'Incerto', 'level.scartato': 'Scartato',
    'd.autoSimilar': 'Segnala anche modelli quasi uguali, se manca una sola parola del nome',
    'd.exclude': 'Parole da escludere', 'd.excludeHint': 'Usato, ricondizionato, accessori comuni e computer interi sono già scartati, in molte lingue.', 'd.pages': 'Pagine da controllare direttamente', 'd.pagesHint': 'Facoltativo: link di pagine prodotto, per negozi non in elenco.',
    'd.try': 'Prova un’offerta', 'd.tryHint': 'Incolla il titolo di un’offerta per vedere come verrebbe giudicata.', 'd.tryTitle': 'Titolo dell’offerta', 'd.tryPrice': 'Prezzo', 'd.tryBtn': 'Prova',
    'd.active': 'Attivo', 'd.save': 'Salva', 'd.cancel': 'Annulla', 'd.delete': 'Elimina', 'd.confirmDelete': 'Eliminare questo prodotto?', 'd.nameMissing': 'Scrivi il nome del prodotto.',
    'sites.title': 'Siti e canali', 'sites.sub': 'Siti di tutto il mondo, non solo del tuo Paese. Attivali, spegnili, toglili o aggiungine di tuoi. L’esito indica l’ultima prova reale.', 'sites.note.trovaprezzi': 'Blocca la ricerca, ma le sue offerte arrivano da Trovaprezzi', 'sites.note.pagine': 'Blocca la ricerca: incolla i link dei prodotti nella finestra del prodotto', 'sites.note.bloccato': 'Blocca la ricerca automatica', 'sites.worldwide': 'Internazionali', 'sites.siteCountry': 'Paese del sito', 'sites.allOn': 'Attiva tutti quelli che funzionano', 'sites.allOff': 'Spegni tutti', 'sites.restore': 'Ripristina i siti tolti ({n})', 'sites.country': 'Paese', 'sites.all': 'Tutti i Paesi', 'sites.search': 'Cerca un sito', 'sites.onlyActive': 'Solo attivi',
    'sites.test': 'Prova', 'sites.testing': 'Prova…', 'sites.remove': 'Rimuovi', 'sites.none': 'Nessun sito con questi filtri.', 'sites.activeCount': '{n} attivi',
    'status.ok': 'Funziona', 'status.bloccato': 'Bloccato', 'status.vuoto': 'Nessun risultato', 'status.errore': 'Errore', 'status.none': 'Non provato',
    'sites.otherCurrency': 'I prezzi di questo sito vengono convertiti in {c}. Dogana e commissioni escluse.', 'sites.currency': 'Valuta del sito', 'sites.addTitle': 'Aggiungi un sito',
    'sites.addSteps': ['Apri il sito e cerca una parola qualsiasi.', 'Copia l’indirizzo della pagina dei risultati e incollalo qui.', 'Scrivi la parola che hai cercato.'],
    'sites.url': 'Indirizzo dei risultati', 'sites.term': 'Parola cercata', 'sites.name': 'Nome (facoltativo)', 'sites.add': 'Prova e aggiungi', 'sites.badTerm': 'Non trovo la parola cercata nell’indirizzo. Puoi anche scrivere {q} nell’indirizzo al posto della parola.',
    'sites.added': 'Sito aggiunto: {r}', 'sites.addedEmpty': 'Sito aggiunto, ma la prova non ha letto offerte: può servire un altro indirizzo.',
    'tg.title': 'Canali Telegram', 'tg.sub': 'Solo canali pubblici. Per ogni prodotto cerca nel canale i tuoi termini.', 'tg.add': 'Aggiungi', 'tg.placeholder': '@nome o link t.me', 'tg.suggested': 'Consigliati per il tuo Paese:', 'tg.badChannel': 'Canale non valido o non pubblico.',
    'auto.title': 'Esecuzione', 'auto.sub': 'Gira in sottofondo. A computer spento il giro salta e riparte all’orario successivo.', 'auto.every': 'Ogni quante ore', 'auto.hours': 'ore', 'auto.on': 'Avvio automatico', 'auto.next': 'Prossimo giro: {w}', 'auto.times': 'Orari: {t}',
    'auto.est': 'Ogni giro: circa {r} richieste, {m} min.', 'auto.heavy': 'Sono molte richieste. Per non pesare sui siti riduci termini di ricerca o siti attivi.', 'auto.now': 'Fai un giro adesso', 'auto.running': 'Giro in corso…', 'auto.noProducts': 'Aggiungi prima un prodotto.', 'auto.finished': 'Giro finito.',
    'auto.open': 'Apri il report nel browser a fine giro', 'auto.log': 'Ultime righe del registro',
    'eb.title': 'eBay ufficiale', 'eb.sub': 'Con una chiave gratuita eBay entra da solo in ogni giro, senza Chrome. Su developer.ebay.com crea un account sviluppatore e una chiave “Production”, poi copia App ID e Cert ID qui. Restano solo sul tuo computer.', 'eb.app': 'App ID', 'eb.cert': 'Cert ID', 'eb.test': 'Prova e salva', 'eb.ok': 'Funziona: {t}', 'eb.none': 'Chiave valida, ma nessun risultato di prova.', 'eb.country': 'eBay non ha un mercato per questo Paese.', 'open.title': 'Controlla a mano', 'open.sub': 'Questi negozi bloccano le ricerche automatiche. Un clic apre la ricerca nel tuo browser: qui l’app non legge nulla.', 'ai.title': 'IA locale', 'ai.sub': 'Controlla solo le offerte dubbie e gira sul tuo computer: non esce nulla. Riconosce accessori e computer interi e legge i valori non capiti dalle regole. Circa 5 secondi a offerta su un portatile; i titoli già visti non si ricontrollano.', 'ai.on': 'Usa l’IA locale', 'ai.model': 'Modello', 'ai.auto': 'Scelta automatica', 'ai.ready': 'Ollama è attivo.', 'ai.noModel': 'Ollama è attivo ma senza modelli. Installane uno con: ollama pull {m}', 'ai.off': 'Ollama non è attivo: i giri usano solo le regole. Si scarica da ollama.com, poi: ollama pull {m}', 'set.title': 'Impostazioni', 'set.region': 'Lingua e Paese', 'set.lang': 'Lingua', 'set.country': 'Paese', 'set.currency': 'Valuta', 'set.rates': 'Gli altri prezzi vengono convertiti in {c} col cambio della Banca Centrale Europea del {d}.', 'set.noRates': 'Cambi non ancora scaricati: senza cambio i siti in un’altra valuta vengono saltati.', 'set.activate': 'Attiva i siti funzionanti di questo Paese', 'set.activated': 'Siti attivati: {n}',
    'set.tg': 'Notifiche su Telegram', 'set.tgSteps': ['Su Telegram scrivi a @BotFather, invia /newbot e copia il token.', 'Incollalo qui e scrivi un messaggio al tuo nuovo bot.', 'Premi “Trova il mio chat id”, poi “Invia una prova”.'],
    'set.token': 'Token del bot', 'set.chat': 'Chat id', 'set.findId': 'Trova il mio chat id', 'set.sendTest': 'Invia una prova', 'set.noChat': 'Nessun messaggio trovato: scrivi al bot e riprova.', 'set.sent': 'Messaggio inviato.',
    'set.summary': 'A fine giro invia su Telegram le offerte migliori e il report completo', 'set.shops': 'Negozi da considerare dubbi', 'set.shopsHint': 'Scelti solo se non c’è altro.',
    'results.title': 'Risultati', 'results.none': 'Ancora nessun risultato: fai un giro da “Esecuzione”.', 'results.open': 'Apri in una nuova scheda',
    'saved': 'Salvato', 'error': 'Errore: {e}', 'on': 'Attivo', 'off': 'Spento',
  },
  en: {
    'nav.products': 'Products', 'nav.sites': 'Sites & channels', 'nav.auto': 'Schedule', 'nav.results': 'Results', 'nav.settings': 'Settings',
    'products.title': 'Products', 'products.sub': 'What you want to track. Each product has its own specs and margins.',
    'products.add': 'Add product', 'products.off': 'Paused', 'products.max': 'up to', 'products.alert': 'alert below',
    'products.terms': 'searches', 'products.empty': 'Press + to add your first product.',
    'd.new': 'New product', 'd.edit': 'Edit product', 'd.name': 'Product you want', 'd.nameHint': 'Brand and model, for example: RTX 5070 Ti, Sony WH-1000XM5. Values such as 1TB, 32GB or CL30 in the name count as a minimum or maximum: a better value is flagged as better.',
    'd.search': 'Search terms on the sites', 'd.searchHint': 'Press Enter after each term. If empty, it searches the product name. Each term adds one request per site.',
    'd.specs': 'Required specs', 'd.specsHint': 'Read from the offer title. With a margin, a slightly different value stays valid and is flagged as similar. Beyond the margin the offer is discarded.',
    'd.specName': 'Name', 'd.specOp': 'Condition', 'd.specValue': 'Value', 'd.specUnit': 'Unit', 'd.specMargin': 'Margin %', 'd.addSpec': '+ Add spec',
    'op.min': 'at least', 'op.max': 'at most', 'op.eq': 'equal to', 'op.text': 'contains',
    'd.price': 'Price', 'd.min': 'Minimum', 'd.max': 'Maximum', 'd.alert': 'Alert me below', 'd.priceHint': 'The minimum removes accessories and wrong prices: worth setting.',
    'd.alts': 'Also acceptable', 'd.altsHint': 'Other models you would accept. Results flag them as similar or better.', 'd.altText': 'Model', 'd.addAlt': '+ Add model',
    'level.simile': 'Similar', 'level.superiore': 'Better', 'level.esatto': 'Exact', 'level.incerto': 'Uncertain', 'level.scartato': 'Discarded',
    'd.autoSimilar': 'Also flag near-identical models when one word of the name is missing',
    'd.exclude': 'Words to exclude', 'd.excludeHint': 'Used, refurbished, common accessories and whole computers are already discarded, in many languages.', 'd.pages': 'Pages to check directly', 'd.pagesHint': 'Optional: product page links, for shops not in the list.',
    'd.try': 'Try an offer', 'd.tryHint': 'Paste an offer title to see how it would be judged.', 'd.tryTitle': 'Offer title', 'd.tryPrice': 'Price', 'd.tryBtn': 'Try',
    'd.active': 'Active', 'd.save': 'Save', 'd.cancel': 'Cancel', 'd.delete': 'Delete', 'd.confirmDelete': 'Delete this product?', 'd.nameMissing': 'Enter the product name.',
    'sites.title': 'Sites & channels', 'sites.sub': 'Sites from all over the world, not only your country. Turn them on or off, remove them or add your own. The status shows the latest real test.', 'sites.note.trovaprezzi': 'Blocks searches, but its offers arrive through Trovaprezzi', 'sites.note.pagine': 'Blocks searches: paste product links in the product window', 'sites.note.bloccato': 'Blocks automatic searches', 'sites.worldwide': 'International', 'sites.siteCountry': 'Site country', 'sites.allOn': 'Turn on all that work', 'sites.allOff': 'Turn all off', 'sites.restore': 'Restore removed sites ({n})', 'sites.country': 'Country', 'sites.all': 'All countries', 'sites.search': 'Find a site', 'sites.onlyActive': 'Active only',
    'sites.test': 'Test', 'sites.testing': 'Testing…', 'sites.remove': 'Remove', 'sites.none': 'No sites match these filters.', 'sites.activeCount': '{n} active',
    'status.ok': 'Works', 'status.bloccato': 'Blocked', 'status.vuoto': 'No results', 'status.errore': 'Error', 'status.none': 'Not tested',
    'sites.otherCurrency': 'Prices from this site are converted to {c}. Customs and fees not included.', 'sites.currency': 'Site currency', 'sites.addTitle': 'Add a site',
    'sites.addSteps': ['Open the site and search for any word.', 'Copy the address of the results page and paste it here.', 'Type the word you searched for.'],
    'sites.url': 'Results address', 'sites.term': 'Word searched', 'sites.name': 'Name (optional)', 'sites.add': 'Test and add', 'sites.badTerm': 'I cannot find that word in the address. You can also write {q} in the address in place of the word.',
    'sites.added': 'Site added: {r}', 'sites.addedEmpty': 'Site added, but the test read no offers: it may need a different address.',
    'tg.title': 'Telegram channels', 'tg.sub': 'Public channels only. For each product it searches the channel for your terms.', 'tg.add': 'Add', 'tg.placeholder': '@name or t.me link', 'tg.suggested': 'Suggested for your country:', 'tg.badChannel': 'Invalid or non-public channel.',
    'auto.title': 'Schedule', 'auto.sub': 'Runs in the background. If the computer is off the run is skipped and it resumes at the next time.', 'auto.every': 'Run every', 'auto.hours': 'hours', 'auto.on': 'Automatic runs', 'auto.next': 'Next run: {w}', 'auto.times': 'Times: {t}',
    'auto.est': 'Each run: about {r} requests, {m} min.', 'auto.heavy': 'That is a lot of requests. To go easy on the sites, reduce search terms or active sites.', 'auto.now': 'Run now', 'auto.running': 'Run in progress…', 'auto.noProducts': 'Add a product first.', 'auto.finished': 'Run finished.',
    'auto.open': 'Open the report in the browser after each run', 'auto.log': 'Latest log lines',
    'eb.title': 'Official eBay', 'eb.sub': 'With a free key, eBay joins every run on its own, without Chrome. On developer.ebay.com create a developer account and a “Production” key, then copy the App ID and Cert ID here. They stay on your computer.', 'eb.app': 'App ID', 'eb.cert': 'Cert ID', 'eb.test': 'Test and save', 'eb.ok': 'It works: {t}', 'eb.none': 'The key is valid, but the test found nothing.', 'eb.country': 'eBay has no marketplace for this country.', 'open.title': 'Check by hand', 'open.sub': 'These shops block automatic searches. One click opens the search in your browser: the app reads nothing there.', 'ai.title': 'Local AI', 'ai.sub': 'Checks only doubtful offers and runs on your computer: nothing leaves it. It spots accessories and whole computers and reads values the rules miss. About 5 seconds per offer on a laptop; titles already seen are not checked again.', 'ai.on': 'Use the local AI', 'ai.model': 'Model', 'ai.auto': 'Automatic', 'ai.ready': 'Ollama is running.', 'ai.noModel': 'Ollama is running but has no models. Install one with: ollama pull {m}', 'ai.off': 'Ollama is not running: runs use only the rules. Get it from ollama.com, then: ollama pull {m}', 'set.title': 'Settings', 'set.region': 'Language and country', 'set.lang': 'Language', 'set.country': 'Country', 'set.currency': 'Currency', 'set.rates': 'Other prices are converted to {c} at the European Central Bank rate of {d}.', 'set.noRates': 'Exchange rates not downloaded yet: without a rate, sites in another currency are skipped.', 'set.activate': 'Turn on working sites for this country', 'set.activated': 'Sites turned on: {n}',
    'set.tg': 'Telegram notifications', 'set.tgSteps': ['On Telegram message @BotFather, send /newbot and copy the token.', 'Paste it here and send a message to your new bot.', 'Press “Find my chat id”, then “Send a test”.'],
    'set.token': 'Bot token', 'set.chat': 'Chat id', 'set.findId': 'Find my chat id', 'set.sendTest': 'Send a test', 'set.noChat': 'No messages found: message the bot and try again.', 'set.sent': 'Message sent.',
    'set.summary': 'After each run, send the best offers and the full report on Telegram', 'set.shops': 'Shops to treat as doubtful', 'set.shopsHint': 'Picked only when nothing else is available.',
    'results.title': 'Results', 'results.none': 'No results yet: start a run from “Schedule”.', 'results.open': 'Open in a new tab',
    'saved': 'Saved', 'error': 'Error: {e}', 'on': 'On', 'off': 'Off',
  },
};
const UNITS = ['GB', 'TB', 'MB', 'GHz', 'MHz', 'Hz', 'W', 'kW', 'mm', 'cm', 'inch', 'kg', 'g', 'mAh', 'l', 'CL'];
const TOKEN = document.querySelector('meta[name=pw-token]').content;
const $ = (id) => document.getElementById(id);

let S = null;
let tab = 'products';
const filters = { country: null, search: '', onlyActive: false };
const tested = {};
let pollTimer = null;

function tr(key, vars) {
  const lang = S?.config?.generale?.lingua === 'it' ? 'it' : 'en';
  let text = STRINGS[lang][key] ?? key;
  if (vars) for (const [k, v] of Object.entries(vars)) text = text.replace(`{${k}}`, v);
  return text;
}

/** Creates an element: texts always go through textContent, never innerHTML. */
function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (k === 'value') el.value = v;
    else if (k === 'checked' || k === 'disabled' || k === 'selected') el[k] = true;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) el.append(kid);
  return el;
}

async function api(path, body) {
  const res = await fetch(path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { 'X-PW-Token': TOKEN, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.errore || `HTTP ${res.status}`);
  return data;
}

function toast(text) {
  const t = $('toast');
  t.textContent = text;
  t.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { t.hidden = true; }, 3200);
}
const fail = (e) => toast(tr('error', { e: e.message }));

async function saveConfig(update, quiet) {
  try {
    S = await api('/api/config', update);
    if (!quiet) toast(tr('saved'));
    render();
    return true;
  } catch (e) {
    fail(e);
    return false;
  }
}

function countries(withWorldwide) {
  const names = new Intl.DisplayNames([S.config.generale.lingua === 'it' ? 'it' : 'en'], { type: 'region' });
  const list = S.paesi.filter((c) => c !== 'WW').map((c) => [c, names.of(c)]).sort((a, b) => a[1].localeCompare(b[1]));
  return withWorldwide ? [['WW', tr('sites.worldwide')], ...list] : list;
}

const money = (v) => {
  if (v === null || v === undefined || v === '') return '';
  const cur = S.config.generale.valuta;
  return new Intl.NumberFormat(S.config.generale.lingua === 'it' ? 'it-IT' : 'en-GB', { style: 'currency', currency: cur, maximumFractionDigits: v % 1 ? 2 : 0 }).format(v);
};

// ------------------------------------------------------------------ componenti
function field(label, control, hint) {
  return h('label', { class: 'field' }, label, control, hint ? h('span', { class: 'hint' }, hint) : null);
}

/** List of entries: Enter adds, x removes. values is modified in place. */
function tagInput(values, placeholder) {
  const list = h('div', { class: 'chips' });
  const input = h('input', { placeholder, 'aria-label': placeholder });
  const draw = () => {
    list.replaceChildren(...values.map((v, i) => h('span', { class: 'chip' }, v,
      h('button', { type: 'button', 'aria-label': `✕ ${v}`, onclick: () => { values.splice(i, 1); draw(); } }, '×'))));
  };
  const commit = () => {
    const v = input.value.trim();
    if (v && !values.includes(v)) values.push(v);
    input.value = '';
    draw();
  };
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); commit(); } });
  input.addEventListener('blur', commit);
  draw();
  return h('div', { class: 'block' }, list, input);
}

// ------------------------------------------------------------------ prodotti
function viewProducts() {
  const products = S.config.prodotti;
  const cards = products.map((p) => h('button', { class: `product${p.attivo ? '' : ' off'}`, type: 'button', onclick: () => openProduct(p) },
    h('b', null, p.nome),
    h('div', { class: 'chips' }, p.specifiche.slice(0, 4).map((s) => h('span', { class: 'chip' }, specLabel(s)))),
    h('div', { class: 'muted small' }, [
      p.attivo ? null : tr('products.off'),
      p.prezzo_max ? `${tr('products.max')} ${money(p.prezzo_max)}` : null,
      p.soglia_avviso ? `${tr('products.alert')} ${money(p.soglia_avviso)}` : null,
      `${tr('products.terms')}: ${p.ricerca.length}`,
    ].filter(Boolean).join(' · '))));
  return [
    h('div', { class: 'page-head' }, h('div', null, h('h1', null, tr('products.title')), h('p', { class: 'muted' }, tr('products.sub')))),
    h('div', { class: 'products' }, cards,
      h('button', { class: 'add', type: 'button', onclick: () => openProduct(null), id: 'addProduct' },
        h('span', { class: 'plus', 'aria-hidden': 'true' }, '+'), tr('products.add'))),
    products.length ? null : h('p', { class: 'empty' }, tr('products.empty')),
  ];
}

function specLabel(s) {
  const op = { min: '≥', max: '≤', eq: '=', text: '' }[s.op];
  const margin = Number(s.margine_pct) ? ` ±${s.margine_pct}%` : '';
  return `${s.nome ? s.nome + ' ' : ''}${op} ${s.valore} ${s.unita || ''}${margin}`.replace(/\s+/g, ' ').trim();
}

function openProduct(existing) {
  const p = existing ? structuredClone(existing) : { nome: '', attivo: true, ricerca: [], specifiche: [], alternative: [], esclusi: [], pagine: [], accetta_simili: true, prezzo_min: null, prezzo_max: null, soglia_avviso: null };
  // terms equal to the name must not be shown as the user's choice
  if (p.ricerca.length === 1 && p.ricerca[0] === p.nome) p.ricerca = [];
  const dlg = $('dialog');

  const name = h('input', { value: p.nome, required: true, id: 'pName' });
  const priceInput = (key, label) => field(label, h('input', { inputmode: 'decimal', value: p[key] ?? '', 'data-key': key, oninput: (e) => { p[key] = e.target.value; } }));

  const specsBox = h('div', { class: 'block' });
  const drawSpecs = () => {
    const rows = p.specifiche.map((s, i) => {
      const set = (k) => (e) => { s[k] = e.target.value; };
      const isText = s.op === 'text';
      return h('div', { class: 'spec' },
        h('input', { value: s.nome || '', 'aria-label': tr('d.specName'), placeholder: tr('d.specName'), oninput: set('nome') }),
        h('select', { 'aria-label': tr('d.specOp'), onchange: (e) => { s.op = e.target.value; drawSpecs(); } },
          ['min', 'max', 'eq', 'text'].map((o) => h('option', { value: o, selected: s.op === o }, tr(`op.${o}`)))),
        h('input', { value: s.valore ?? '', 'aria-label': tr('d.specValue'), placeholder: tr('d.specValue'), inputmode: isText ? 'text' : 'decimal', oninput: set('valore') }),
        h('input', { value: s.unita || '', 'aria-label': tr('d.specUnit'), placeholder: tr('d.specUnit'), list: 'units', disabled: isText, oninput: set('unita') }),
        h('input', { value: s.margine_pct || '', 'aria-label': tr('d.specMargin'), placeholder: '%', inputmode: 'decimal', disabled: isText, oninput: set('margine_pct') }),
        h('button', { type: 'button', class: 'icon', 'aria-label': `${tr('d.delete')} ${s.nome || ''}`, onclick: () => { p.specifiche.splice(i, 1); drawSpecs(); } }, '×'));
    });
    specsBox.replaceChildren(
      ...(rows.length ? [h('div', { class: 'spec spec-head' }, ['d.specName', 'd.specOp', 'd.specValue', 'd.specUnit', 'd.specMargin'].map((k) => h('span', null, tr(k))), h('span'))] : []),
      ...rows,
      h('div', null, h('button', { type: 'button', class: 'link', onclick: () => { p.specifiche.push({ nome: '', op: 'min', valore: '', unita: '', margine_pct: 0 }); drawSpecs(); } }, tr('d.addSpec'))));
  };
  drawSpecs();

  const altsBox = h('div', { class: 'block' });
  const drawAlts = () => {
    altsBox.replaceChildren(
      ...p.alternative.map((a, i) => h('div', { class: 'alt' },
        h('input', { value: a.testo, 'aria-label': tr('d.altText'), placeholder: tr('d.altText'), oninput: (e) => { a.testo = e.target.value; } }),
        h('select', { 'aria-label': tr('d.alts'), onchange: (e) => { a.tipo = e.target.value; } },
          ['simile', 'superiore'].map((o) => h('option', { value: o, selected: a.tipo === o }, tr(`level.${o}`)))),
        h('button', { type: 'button', class: 'icon', 'aria-label': tr('d.delete'), onclick: () => { p.alternative.splice(i, 1); drawAlts(); } }, '×'))),
      h('div', null, h('button', { type: 'button', class: 'link', onclick: () => { p.alternative.push({ testo: '', tipo: 'simile' }); drawAlts(); } }, tr('d.addAlt'))));
  };
  drawAlts();

  const tryTitle = h('input', { 'aria-label': tr('d.tryTitle'), placeholder: tr('d.tryTitle') });
  const tryPrice = h('input', { 'aria-label': tr('d.tryPrice'), placeholder: tr('d.tryPrice'), inputmode: 'decimal', class: 'num' });
  const tryResult = h('div', { class: 'result', hidden: true, 'aria-live': 'polite' });
  const collect = () => ({ ...p, nome: name.value.trim(), ricerca: p.ricerca });
  const runTry = async () => {
    if (!name.value.trim()) return toast(tr('d.nameMissing'));
    try {
      const r = await api('/api/try', { prodotto: collect(), titolo: tryTitle.value, prezzo: tryPrice.value });
      const level = r.ok ? r.livello : 'scartato';
      tryResult.replaceChildren(h('span', { class: `lvl ${level}` }, r.ok ? r.etichetta : tr('level.scartato')), r.motivo ? ` ${r.motivo}` : '',
        ...(r.avvisi.length || r.note.length ? [h('ul', null, [...r.note, ...r.avvisi].map((w) => h('li', null, w)))] : []));
      tryResult.hidden = false;
    } catch (e) { fail(e); }
    return null;
  };

  const active = h('input', { type: 'checkbox', checked: p.attivo, onchange: (e) => { p.attivo = e.target.checked; } });
  const form = h('form', { method: 'dialog', novalidate: true, onsubmit: async (e) => {
    e.preventDefault();
    if (!name.value.trim()) { toast(tr('d.nameMissing')); name.focus(); return; }
    const list = S.config.prodotti.filter((x) => x.id !== p.id);
    const data = collect();
    const others = existing ? S.config.prodotti.map((x) => (x.id === p.id ? data : x)) : [...list, data];
    if (await saveConfig({ prodotti: others })) dlg.close();
  } },
  h('div', { class: 'd-head' }, h('h2', null, tr(existing ? 'd.edit' : 'd.new')),
    h('label', { class: 'check' }, active, tr('d.active'))),
  h('div', { class: 'd-body' },
    h('div', { class: 'block' }, field(tr('d.name'), name, tr('d.nameHint'))),
    h('div', { class: 'block' }, h('h3', null, tr('d.specs')), h('span', { class: 'hint' }, tr('d.specsHint')), specsBox),
    h('div', { class: 'block' }, h('h3', null, tr('d.price')), h('span', { class: 'hint' }, tr('d.priceHint')),
      h('div', { class: 'cols' }, priceInput('prezzo_min', `${tr('d.min')} (${S.config.generale.valuta})`), priceInput('prezzo_max', `${tr('d.max')} (${S.config.generale.valuta})`), priceInput('soglia_avviso', `${tr('d.alert')} (${S.config.generale.valuta})`))),
    h('div', { class: 'block' }, h('h3', null, tr('d.alts')), h('span', { class: 'hint' }, tr('d.altsHint')), altsBox,
      h('label', { class: 'check' }, h('input', { type: 'checkbox', checked: p.accetta_simili, onchange: (e) => { p.accetta_simili = e.target.checked; } }), tr('d.autoSimilar'))),
    h('div', { class: 'block' }, h('h3', null, tr('d.search')), h('span', { class: 'hint' }, tr('d.searchHint')), tagInput(p.ricerca, tr('d.search'))),
    h('div', { class: 'block' }, h('h3', null, tr('d.exclude')), h('span', { class: 'hint' }, tr('d.excludeHint')), tagInput(p.esclusi, tr('d.exclude'))),
    h('div', { class: 'block' }, h('h3', null, tr('d.pages')), h('span', { class: 'hint' }, tr('d.pagesHint')), tagInput(p.pagine, 'https://…')),
    h('div', { class: 'block' }, h('h3', null, tr('d.try')), h('span', { class: 'hint' }, tr('d.tryHint')),
      h('div', { class: 'row' }, h('div', { class: 'grow' }, tryTitle), tryPrice, h('button', { type: 'button', class: 'btn', onclick: runTry }, tr('d.tryBtn'))), tryResult)),
  h('div', { class: 'd-foot' },
    existing ? h('button', { type: 'button', class: 'btn danger', onclick: async () => {
      if (!confirm(tr('d.confirmDelete'))) return;
      if (await saveConfig({ prodotti: S.config.prodotti.filter((x) => x.id !== p.id) })) dlg.close();
    } }, tr('d.delete')) : h('span'),
    h('div', { class: 'row' }, h('button', { type: 'button', class: 'btn', onclick: () => dlg.close() }, tr('d.cancel')),
      h('button', { type: 'submit', class: 'btn primary', id: 'saveProduct' }, tr('d.save')))),
  h('datalist', { id: 'units' }, UNITS.map((u) => h('option', { value: u }))));
  dlg.replaceChildren(form);
  dlg.showModal();
  name.focus();
}

// ------------------------------------------------------------------ siti
const statusOf = (s) => tested[s.id]?.esito || s.prova?.esito || 'none';

function siteRow(s) {
  const shown = s.valuta_visitatore ? S.config.generale.valuta : s.valuta;
  const currencyOk = shown === S.config.generale.valuta;
  const st = tested[s.id] === 'testing' ? null : statusOf(s);
  const converted = currencyOk ? '' : tr('sites.otherCurrency', { c: S.config.generale.valuta });
  const toggle = h('input', { type: 'checkbox', checked: s.attivo, 'aria-label': s.nome, title: converted,
    onchange: (e) => {
      const active = new Set(S.config.siti.attivi);
      if (e.target.checked) active.add(s.id); else active.delete(s.id);
      saveConfig({ siti: { attivi: [...active] } }, true);
    } });
  const detail = s.prova?.dettaglio || '';
  const test = h('button', { type: 'button', class: 'btn', disabled: tested[s.id] === 'testing', onclick: async () => {
    tested[s.id] = 'testing';
    render();
    try {
      const r = await api('/api/test-site', { id: s.id });
      tested[s.id] = r;
      S = await api('/api/state');
    } catch (e) { delete tested[s.id]; fail(e); }
    render();
  } }, tested[s.id] === 'testing' ? tr('sites.testing') : tr('sites.test'));
  return h('div', { class: `site${s.attivo ? '' : ' off'}` }, toggle,
    h('span', { class: 'name' }, s.nome, s.nota ? h('small', { class: 'muted', style: 'display:block;font-weight:400' }, tr(`sites.note.${s.nota}`)) : null),
    h('span', { class: 'cc muted small' }, s.paese), h('span', { class: 'cur muted small', title: converted }, shown),
    tested[s.id] === 'testing' ? h('span', { class: 'pill none' }, tr('sites.testing')) : h('span', { class: `pill ${st}`, title: detail }, tr(`status.${st}`)),
    h('span', { class: 'actions row' }, test, h('button', { type: 'button', class: 'icon', 'aria-label': `${tr('sites.remove')} ${s.nome}`, title: tr('sites.remove'), onclick: () => {
      const attivi = S.config.siti.attivi.filter((x) => x !== s.id);
      if (s.personalizzato) saveConfig({ siti: { personalizzati: S.config.siti.personalizzati.filter((x) => x.id !== s.id), attivi } });
      else saveConfig({ siti: { rimossi: [...(S.config.siti.rimossi || []), s.id], attivi } });
    } }, '×')));
}

function viewSites() {
  const g = S.config.generale;
  filters.country = filters.country ?? 'all';
  const removed = S.config.siti.rimossi || [];
  const q = filters.search.toLowerCase();
  const isHome = (s) => Number(s.paese === g.paese);
  const list = S.siti.filter((s) => !s.rimosso && (filters.country === 'all' || s.paese === filters.country || s.personalizzato)
    && (!q || s.nome.toLowerCase().includes(q)) && (!filters.onlyActive || s.attivo))
    .sort((a, b) => (b.attivo - a.attivo) || (isHome(b) - isHome(a)) || (Number(statusOf(b) === 'ok') - Number(statusOf(a) === 'ok')) || a.nome.localeCompare(b.nome));
  const listBox = h('div', { class: 'sites', id: 'sites' }, list.length ? list.map(siteRow) : h('p', { class: 'empty' }, tr('sites.none')));
  return [
    h('div', { class: 'page-head' }, h('div', null, h('h1', null, tr('sites.title')), h('p', { class: 'muted' }, tr('sites.sub'))),
      h('span', { class: 'muted small' }, tr('sites.activeCount', { n: S.siti.filter((s) => s.attivo).length }))),
    h('section', { class: 'card' },
      h('div', { class: 'filters' },
        h('select', { 'aria-label': tr('sites.country'), id: 'siteCountry', onchange: (e) => { filters.country = e.target.value; render(); } },
          h('option', { value: 'all', selected: filters.country === 'all' }, tr('sites.all')),
          countries(true).map(([c, n]) => h('option', { value: c, selected: filters.country === c }, n))),
        h('input', { placeholder: tr('sites.search'), 'aria-label': tr('sites.search'), value: filters.search, id: 'siteSearch', oninput: (e) => { filters.search = e.target.value; render(); document.getElementById('siteSearch').focus(); } }),
        h('label', { class: 'check' }, h('input', { type: 'checkbox', checked: filters.onlyActive, onchange: (e) => { filters.onlyActive = e.target.checked; render(); } }), tr('sites.onlyActive'))),
      h('div', { class: 'row', style: 'margin-bottom:10px' },
        h('button', { type: 'button', class: 'btn', id: 'sitesAllOn', onclick: () => saveConfig({ siti: { attivi: S.siti.filter((s) => s.attivo || (!s.rimosso && statusOf(s) === 'ok')).map((s) => s.id) } }, true) }, tr('sites.allOn')),
        h('button', { type: 'button', class: 'btn', id: 'sitesAllOff', onclick: () => saveConfig({ siti: { attivi: [] } }, true) }, tr('sites.allOff')),
        removed.length ? h('button', { type: 'button', class: 'btn', id: 'sitesRestore', onclick: () => saveConfig({ siti: { rimossi: [] } }, true) }, tr('sites.restore', { n: removed.length })) : null),
      listBox),
    addSiteCard(),
    telegramCard(),
  ];
}

function addSiteCard() {
  const url = h('input', { placeholder: 'https://…', id: 'newSiteUrl' });
  const term = h('input', { id: 'newSiteTerm' });
  const name = h('input', { id: 'newSiteName' });
  const country = h('select', { id: 'newSiteCountry' }, countries(true).map(([c, n]) => h('option', { value: c, selected: c === S.config.generale.paese }, n)));
  const currency = h('select', { id: 'newSiteCurrency' }, S.valute.map((c) => h('option', { value: c, selected: c === S.config.generale.valuta }, c)));
  const button = h('button', { type: 'button', class: 'btn primary', onclick: async () => {
    let address = url.value.trim();
    const word = term.value.trim();
    if (!address.includes('{q}')) {
      const forms = [encodeURIComponent(word), word.replace(/\s+/g, '+'), word.replace(/\s+/g, '%20'), word];
      const form = word && forms.find((x) => address.includes(x));
      if (!form) return toast(tr('sites.badTerm'));
      address = address.replace(form, '{q}');
    }
    const g = S.config.generale;
    const site = { url: address, nome: name.value.trim(), paese: country.value, valuta: currency.value };
    button.disabled = true;
    try {
      const result = await api('/api/test-site', { ...site, query: word || undefined });
      const custom = [...S.config.siti.personalizzati, site];
      S = await api('/api/config', { siti: { personalizzati: custom } });
      const added = S.config.siti.personalizzati.at(-1);
      S = await api('/api/config', { siti: { attivi: [...S.config.siti.attivi, added.id], esiti: { [added.id]: result } } });
      toast(result.esito === 'ok' ? tr('sites.added', { r: result.esempio || added.nome }) : tr('sites.addedEmpty'));
      render();
    } catch (e) { fail(e); button.disabled = false; }
    return null;
  } }, tr('sites.add'));
  return h('section', { class: 'card' }, h('h2', null, tr('sites.addTitle')),
    h('ol', { class: 'steps' }, tr('sites.addSteps').map((x) => h('li', null, x))),
    h('div', { class: 'block' }, field(tr('sites.url'), url),
      h('div', { class: 'cols' }, field(tr('sites.term'), term), field(tr('sites.name'), name), field(tr('sites.siteCountry'), country), field(tr('sites.currency'), currency)),
      h('div', null, button)));
}

function telegramCard() {
  const channels = S.config.telegram.canali;
  const saveChannels = (list) => saveConfig({ telegram: { canali: list } }, true);
  const input = h('input', { placeholder: tr('tg.placeholder'), 'aria-label': tr('tg.placeholder'), id: 'newChannel' });
  const add = async () => {
    const value = input.value.trim();
    if (!value) return;
    try {
      const r = await api('/api/test-site', { canale: value });
      if (r.esito !== 'ok') return toast(tr('tg.badChannel'));
      await saveChannels([...channels, value]);
    } catch { toast(tr('tg.badChannel')); }
  };
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); add(); } });
  const suggested = (S.canali_consigliati[S.config.generale.paese] || []).filter((c) => !channels.includes(c));
  return h('section', { class: 'card' }, h('h2', null, tr('tg.title')), h('p', { class: 'muted small' }, tr('tg.sub')),
    h('div', { class: 'block' },
      h('div', { class: 'row' }, h('div', { class: 'grow' }, input), h('button', { type: 'button', class: 'btn', onclick: add }, tr('tg.add'))),
      h('div', { class: 'chips', id: 'channels' }, channels.map((c) => h('span', { class: 'chip' }, `@${c}`,
        h('button', { type: 'button', 'aria-label': `${tr('sites.remove')} ${c}`, onclick: () => saveChannels(channels.filter((x) => x !== c)) }, '×')))),
      suggested.length ? h('div', { class: 'block' }, h('span', { class: 'hint' }, tr('tg.suggested')),
        h('div', { class: 'chips' }, suggested.map((c) => h('button', { type: 'button', class: 'btn', style: 'padding:2px 8px;font-size:12.5px', onclick: () => saveChannels([...channels, c]) }, `+ @${c}`)))) : null));
}

// ------------------------------------------------------------------ esecuzione
function viewAuto() {
  const g = S.config.generale;
  const plan = S.pianificazione;
  const hours = [];
  for (let x = 0; x < 24; x += Number(g.intervallo_ore)) hours.push(`${String(x).padStart(2, '0')}:00`);
  const when = plan.prossimo ? new Date(plan.prossimo).toLocaleString(g.lingua === 'it' ? 'it-IT' : 'en-GB', { weekday: 'short', hour: '2-digit', minute: '2-digit' }) : '';
  const every = h('input', { type: 'number', min: 1, max: 24, step: 1, value: g.intervallo_ore, class: 'num', id: 'every', 'aria-label': tr('auto.every'),
    onchange: (e) => {
      const value = Math.round(Number(e.target.value));
      if (value >= 1 && value <= 24) saveConfig({ generale: { intervallo_ore: value } });
      else { e.target.value = g.intervallo_ore; toast('1–24'); }
    } });
  const heavy = S.stima.richieste > 150;
  return [
    h('div', { class: 'page-head' }, h('div', null, h('h1', null, tr('auto.title')), h('p', { class: 'muted' }, tr('auto.sub')))),
    h('section', { class: 'card' },
      h('div', { class: 'row', style: 'justify-content:space-between' },
        h('label', { class: 'row', style: 'font-weight:600' }, tr('auto.every'), every, tr('auto.hours')),
        h('label', { class: 'check', style: 'font-weight:600' }, h('input', { type: 'checkbox', id: 'scheduleOn', checked: plan.attiva, disabled: !S.config.prodotti.length, onchange: async (e) => {
          e.target.disabled = true;
          try { S = await api('/api/schedule', { attiva: e.target.checked }); toast(tr('saved')); } catch (err) { fail(err); }
          render();
        } }), tr('auto.on'))),
      h('p', { class: 'muted small', style: 'margin:10px 0 0' }, tr('auto.times', { t: hours.join(' · ') })),
      plan.attiva ? h('p', { class: 'small', style: 'margin:4px 0 0', id: 'nextRun' }, tr('auto.next', { w: when })) : null,
      S.config.prodotti.length ? null : h('p', { class: 'small', style: 'margin:4px 0 0;color:var(--warn)' }, tr('auto.noProducts'))),
    h('section', { class: 'card' },
      h('div', { class: 'row', style: 'justify-content:space-between' },
        h('div', null, h('p', { class: 'small' }, tr('auto.est', { r: S.stima.richieste, m: S.stima.minuti })),
          heavy ? h('p', { class: 'small', style: 'color:var(--warn)' }, tr('auto.heavy')) : null),
        h('button', { type: 'button', class: 'btn primary', id: 'runNow', disabled: S.giro.in_corso || !S.config.prodotti.length, onclick: startRun }, S.giro.in_corso ? tr('auto.running') : tr('auto.now'))),
      h('label', { class: 'check', style: 'margin-top:10px' }, h('input', { type: 'checkbox', checked: g.apri_report, onchange: (e) => saveConfig({ generale: { apri_report: e.target.checked } }) }), tr('auto.open')),
      S.log ? h('div', null, h('p', { class: 'small muted', style: 'margin-top:12px' }, tr('auto.log')), h('pre', { class: 'log', id: 'log' }, S.log)) : null),
  ];
}

async function startRun() {
  try {
    await api('/api/run', {});
    S.giro = { in_corso: true };
    render();
    poll();
  } catch (e) { fail(e); }
}

function poll() {
  clearTimeout(pollTimer);
  pollTimer = setTimeout(async () => {
    try {
      const r = await api('/api/run');
      const was = S.giro.in_corso;
      S.giro = { in_corso: r.in_corso };
      S.log = r.log;
      if (was && !r.in_corso) {
        S = { ...(await api('/api/state')), log: r.log };
        toast(tr('auto.finished'));
      }
      if (!$('dialog').open && tab === 'auto') render();
      updateBadge();
      if (r.in_corso) poll();
    } catch { poll(); }
  }, 2500);
}

// ------------------------------------------------------------------ impostazioni
function viewSettings() {
  const g = S.config.generale;
  const n = S.config.notifiche;
  const token = h('input', { type: 'password', value: n.telegram_token || '', id: 'tgToken', autocomplete: 'off', onchange: (e) => saveConfig({ notifiche: { telegram_token: e.target.value.trim() } }, true) });
  const chat = h('input', { value: n.telegram_chat_id || '', id: 'tgChat', inputmode: 'numeric', autocomplete: 'off', onchange: (e) => saveConfig({ notifiche: { telegram_chat_id: e.target.value.trim() } }, true) });
  const shops = [...(g.negozi_da_verificare || [])];
  const shopsInput = tagInput(shops, tr('set.shops'));
  shopsInput.addEventListener('focusout', () => setTimeout(() => {
    if (JSON.stringify(shops) !== JSON.stringify(g.negozi_da_verificare || [])) saveConfig({ generale: { negozi_da_verificare: shops } }, true);
  }, 0));
  return [
    h('div', { class: 'page-head' }, h('h1', null, tr('set.title'))),
    h('section', { class: 'card' }, h('h2', null, tr('set.region')),
      h('div', { class: 'cols' },
        field(tr('set.lang'), h('select', { id: 'lang', onchange: (e) => saveConfig({ generale: { lingua: e.target.value } }, true) }, h('option', { value: 'it', selected: g.lingua === 'it' }, 'Italiano'), h('option', { value: 'en', selected: g.lingua !== 'it' }, 'English'))),
        field(tr('set.country'), h('select', { id: 'country', onchange: (e) => {
          filters.country = null;
          saveConfig({ generale: { paese: e.target.value, valuta: S.valuta_paese[e.target.value] || g.valuta } });
        } }, countries(false).map(([c, name]) => h('option', { value: c, selected: g.paese === c }, name)))),
        field(tr('set.currency'), h('select', { id: 'currency', onchange: (e) => saveConfig({ generale: { valuta: e.target.value } }) }, S.valute.map((c) => h('option', { value: c, selected: g.valuta === c }, c))))),
      h('p', { class: 'muted small', id: 'ratesNote', style: 'margin-top:12px' }, S.cambi ? tr('set.rates', { c: g.valuta, d: new Date(S.cambi).toLocaleDateString(g.lingua === 'it' ? 'it-IT' : 'en-GB') }) : tr('set.noRates')),
      h('div', { style: 'margin-top:12px' }, h('button', { type: 'button', class: 'btn', onclick: () => {
        const working = S.siti.filter((s) => s.paese === g.paese && !s.rimosso && s.prova?.esito === 'ok').map((s) => s.id);
        saveConfig({ siti: { attivi: [...new Set([...S.config.siti.attivi, ...working])] } }, true).then(() => toast(tr('set.activated', { n: working.length })));
      } }, tr('set.activate')))),
    h('section', { class: 'card' }, h('h2', null, tr('set.tg')),
      h('ol', { class: 'steps' }, tr('set.tgSteps').map((x) => h('li', null, x))),
      h('div', { class: 'cols' }, field(tr('set.token'), token), field(tr('set.chat'), chat)),
      h('div', { class: 'row', style: 'margin-top:12px' },
        h('button', { type: 'button', class: 'btn', onclick: async () => {
          try {
            const r = await api('/api/telegram-id', { telegram_token: token.value.trim() });
            if (!r.ids.length) return toast(tr('set.noChat'));
            chat.value = r.ids[0].split(/\s+/)[0];
            await saveConfig({ notifiche: { telegram_token: token.value.trim(), telegram_chat_id: chat.value } });
          } catch (e) { fail(e); }
          return null;
        } }, tr('set.findId')),
        h('button', { type: 'button', class: 'btn', onclick: async () => {
          try {
            const r = await api('/api/telegram-test', { telegram_token: token.value.trim(), telegram_chat_id: chat.value.trim() });
            toast(r.esito === 'ok' ? tr('set.sent') : r.esito);
          } catch (e) { fail(e); }
        } }, tr('set.sendTest'))),
      h('label', { class: 'check', style: 'margin-top:12px' }, h('input', { type: 'checkbox', checked: n.riepilogo, onchange: (e) => saveConfig({ notifiche: { riepilogo: e.target.checked } }) }), tr('set.summary'))),
    ebayCard(),
    aiCard(g),
    h('section', { class: 'card' }, h('h2', null, tr('set.shops')), h('p', { class: 'muted small' }, tr('set.shopsHint')), shopsInput),
  ];
}

function ebayCard() {
  const keys = S.config.ebay || {};
  const app = h('input', { id: 'ebayApp', value: keys.app_id || '', autocomplete: 'off' });
  const cert = h('input', { id: 'ebayCert', type: 'password', value: keys.cert_id || '', autocomplete: 'off' });
  return h('section', { class: 'card' }, h('h2', null, tr('eb.title')), h('p', { class: 'muted small' }, tr('eb.sub')),
    h('div', { class: 'cols' }, field(tr('eb.app'), app), field(tr('eb.cert'), cert)),
    h('div', { style: 'margin-top:12px' }, h('button', { type: 'button', class: 'btn', id: 'ebayTest', onclick: async () => {
      const update = { app_id: app.value.trim(), cert_id: cert.value.trim() };
      try {
        const r = await api('/api/ebay-test', update);
        await saveConfig({ ebay: update }, true);
        if (r.esito === 'paese') return toast(tr('eb.country'));
        toast(r.esito !== 'ok' ? r.esito : r.letti ? tr('eb.ok', { t: r.esempio }) : tr('eb.none'));
      } catch (e) { fail(e); }
      return null;
    } }, tr('eb.test'))));
}

function openByHandCard() {
  const shops = S.siti.filter((s) => s.nota && !s.rimosso);
  const products = S.config.prodotti.filter((p) => p.attivo !== false);
  if (!shops.length || !products.length) return null;
  return h('section', { class: 'card', id: 'openByHand' }, h('h2', null, tr('open.title')), h('p', { class: 'muted small' }, tr('open.sub')),
    products.map((p) => h('div', { class: 'row', style: 'margin-top:8px' }, h('span', { class: 'small' }, p.nome),
      shops.map((s) => h('a', { class: 'btn', target: '_blank', rel: 'noopener', href: s.url.replace('{q}', encodeURIComponent((p.ricerca || [p.nome])[0])) }, s.nome)))));
}

function aiCard(g) {
  const note = h('p', { class: 'muted small', id: 'aiNote' });
  const model = h('select', { id: 'aiModel', 'aria-label': tr('ai.model'), onchange: (e) => saveConfig({ generale: { ia_modello: e.target.value } }, true) }, h('option', { value: '' }, tr('ai.auto')));
  api('/api/ai').then((st) => {
    const suggested = 'qwen2.5vl:3b';
    note.textContent = !st.attiva ? tr('ai.off', { m: suggested }) : st.modelli.length ? tr('ai.ready') : tr('ai.noModel', { m: suggested });
    model.append(...st.modelli.map((m) => h('option', { value: m, selected: g.ia_modello === m }, m)));
  }).catch(fail);
  return h('section', { class: 'card' }, h('h2', null, tr('ai.title')), h('p', { class: 'muted small' }, tr('ai.sub')),
    h('label', { class: 'check' }, h('input', { type: 'checkbox', id: 'aiOn', checked: g.ia_attiva, onchange: (e) => saveConfig({ generale: { ia_attiva: e.target.checked } }, true) }), tr('ai.on')),
    h('div', { class: 'cols', style: 'margin-top:10px' }, field(tr('ai.model'), model)), note);
}

function viewResults() {
  if (!S.report) return [h('div', { class: 'page-head' }, h('h1', null, tr('results.title'))), h('p', { class: 'empty' }, tr('results.none'))];
  return [
    h('div', { class: 'page-head' }, h('h1', null, tr('results.title')), h('a', { class: 'btn', href: '/report', target: '_blank', rel: 'noopener' }, tr('results.open'))),
    openByHandCard(),
    h('iframe', { class: 'frame', src: `/report?${S.report_data}`, title: tr('results.title'), sandbox: 'allow-popups allow-popups-to-escape-sandbox' }),
  ];
}

// ------------------------------------------------------------------ guscio
const VIEWS = { products: viewProducts, sites: viewSites, auto: viewAuto, results: viewResults, settings: viewSettings };

function updateBadge() {
  const badge = $('runBadge');
  badge.hidden = !S.giro.in_corso;
  badge.textContent = tr('auto.running');
}

function render() {
  document.documentElement.lang = S.config.generale.lingua === 'it' ? 'it' : 'en';
  $('langBox').replaceChildren(h('select', { id: 'sideLang', 'aria-label': 'Language', onchange: (e) => saveConfig({ generale: { lingua: e.target.value } }, true) },
    h('option', { value: 'en', selected: S.config.generale.lingua !== 'it' }, 'English'), h('option', { value: 'it', selected: S.config.generale.lingua === 'it' }, 'Italiano')));
  $('nav').replaceChildren(...['products', 'sites', 'auto', 'results', 'settings'].map((id) => h('button', { type: 'button', 'aria-current': tab === id ? 'page' : null, id: `nav-${id}`, onclick: async () => {
    tab = id;
    if (id === 'auto') {
      try { S.log = (await api('/api/run')).log; } catch { /* the log is optional */ }
    }
    render();
  } }, tr(`nav.${id}`))));
  const scroll = window.scrollY;
  const main = $('main');
  main.replaceChildren(...VIEWS[tab]().flat().filter(Boolean));
  window.scrollTo(0, scroll);
  updateBadge();
}

(async () => {
  S = await api('/api/state');
  render();
  if (S.giro.in_corso) poll();
})().catch((e) => { document.body.textContent = e.message; });
