"""Tests each catalogue site with a single search and saves the result in pw/catalog_status.json."""
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


# with --ripeti it retries, slowly, the sites that did not work: many requests at once trigger the blocks;
# with --nuovi it tests only sites never tested
status_file = ROOT / "pw" / "catalog_status.json"
old = json.loads(status_file.read_text(encoding="utf-8")) if status_file.exists() else {}
todo = [s for s in SITES if old.get(s["id"], {}).get("esito") != "ok"] if "--ripeti" in sys.argv else SITES
if "--nuovi" in sys.argv:
    todo = [s for s in SITES if s["id"] not in old]
if "--ids" in sys.argv:  # only the given sites: --ids unieuro,bpm
    wanted = sys.argv[sys.argv.index("--ids") + 1].split(",")
    todo = [s for s in SITES if s["id"] in wanted]
if "--browser" in sys.argv:  # sites that open with the invisible browser, one at a time
    todo = [s for s in SITES if s.get("browser")]
with ThreadPoolExecutor(max_workers=1 if "--ripeti" in sys.argv or "--browser" in sys.argv else 6) as ex:
    results = {**old, **dict(ex.map(one, todo))}
status_file.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print(Counter(r["esito"] for r in results.values()), len(results))
