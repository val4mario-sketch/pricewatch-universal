"""Prova ogni sito del catalogo con una sola ricerca e salva l'esito in pw/catalog_status.json."""
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pw.catalog import SITES  # noqa: E402
from pw.sitetest import test_site  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def one(site):
    res = test_site(site)
    res["data"] = date.today().isoformat()
    print(f"{site['id']:20} {site['paese']} {res['esito']:9} letti {res['letti']:3} pertinenti {res['pertinenti']:3} "
          f"{res.get('prezzo') or '':>9} {str(res.get('esempio') or res['dettaglio'])[:60]}", flush=True)
    return site["id"], res


# con --ripeti riprova, lentamente, i siti che non hanno funzionato: tante richieste insieme fanno scattare i blocchi;
# con --nuovi prova solo i siti mai provati
status_file = ROOT / "pw" / "catalog_status.json"
old = json.loads(status_file.read_text(encoding="utf-8")) if status_file.exists() else {}
todo = [s for s in SITES if old.get(s["id"], {}).get("esito") != "ok"] if "--ripeti" in sys.argv else SITES
if "--nuovi" in sys.argv:
    todo = [s for s in SITES if s["id"] not in old]
if "--ids" in sys.argv:  # solo i siti indicati: --ids unieuro,bpm
    wanted = sys.argv[sys.argv.index("--ids") + 1].split(",")
    todo = [s for s in SITES if s["id"] in wanted]
if "--browser" in sys.argv:  # i siti che si aprono col browser invisibile, uno alla volta
    todo = [s for s in SITES if s.get("browser")]
with ThreadPoolExecutor(max_workers=1 if "--ripeti" in sys.argv or "--browser" in sys.argv else 6) as ex:
    results = {**old, **dict(ex.map(one, todo))}
status_file.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print(Counter(r["esito"] for r in results.values()), len(results))
