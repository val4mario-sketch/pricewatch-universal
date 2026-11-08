"""Local GUI: serves the page and the APIs on this PC only (127.0.0.1)."""
from __future__ import annotations

import json
import secrets
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import ai, catalog, ebay, notify, rates, runner, schedule, settings, sitetest
from .i18n import t
from .rules import Rules

GUI = Path(__file__).with_name("gui")
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}
TOKEN = secrets.token_urlsafe(24)  # other pages open in the browser cannot call the APIs without this
_run_lock = threading.Lock()
_proc: subprocess.Popen | None = None
_plan_active: bool | None = None  # chiedere a Windows richiede circa un secondo: basta farlo una volta


def plan_status(every) -> dict:
    global _plan_active
    if _plan_active is None:
        _plan_active = schedule.status()["attiva"]
    plan = {"attiva": _plan_active}
    if _plan_active:
        plan["prossimo"] = schedule.next_run(int(every)).isoformat(timespec="minutes")
    return plan


def estimate(cfg: dict) -> dict:
    tasks, skipped = runner.build_tasks(cfg, table=rates.cached())
    hosts: dict[str, int] = {}
    for x in tasks:
        host = x.url.split("/")[2]
        hosts[host] = hosts.get(host, 0) + 1
    # average 4.5 s pause per site: up to 8 different sites run in parallel
    minutes = round((max(max(hosts.values(), default=0), len(tasks) / 8) * 4.5 + sum(x.browser for x in tasks) * 9) / 60 + 0.5)
    return {"richieste": len(tasks), "minuti": minutes, "valuta_diversa": sorted(skipped)}


def run_status() -> dict:
    running = _proc is not None and _proc.poll() is None
    lock = settings.DATA / "run.lock"
    return {"in_corso": running or lock.exists()}


def log_tail(lines: int = 40) -> str:
    path = settings.DATA / "pricewatch.log"
    if not path.exists():
        return ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        return "".join(fh.readlines()[-lines:])


def state() -> dict:
    cfg = settings.load()
    every = cfg["generale"].get("intervallo_ore", 3)
    report = settings.DATA / "report.html"
    table = rates.cached()
    return {"cambi": table and table["data"], "config": cfg, "siti": catalog.site_list(cfg), "paesi": catalog.COUNTRIES, "valute": sorted(set(catalog.CURRENCY_OF.values())),
            "valuta_paese": catalog.CURRENCY_OF, "canali_consigliati": catalog.SUGGESTED_CHANNELS, "stima": estimate(cfg),
            "pianificazione": plan_status(every), "giro": run_status(), "report": report.exists(),
            "report_data": report.stat().st_mtime if report.exists() else None}


def try_title(body: dict) -> dict:
    cfg = settings.load()
    product = settings.clean_product(body["prodotto"])
    probe = {**cfg, "prodotti": [{**product, "attivo": True}]}
    price = settings._number(body.get("prezzo"), "price")
    lo = product.get("prezzo_min") or 0
    prices = [price] if price is not None else [max(lo, 1)]  # without a price only the title is tested
    d = Rules(probe).classify(body.get("titolo", ""), prices, hint=product["id"])
    return {"ok": d.ok, "livello": d.level, "etichetta": t(cfg, f"level.{d.level}") if d.level else "", "motivo": d.reason,
            "avvisi": d.warnings, "note": d.tags}


def start_run() -> dict:
    global _proc
    with _run_lock:
        if run_status()["in_corso"]:
            return run_status()
        flags = 0x08000000 if sys.platform == "win32" else 0
        _proc = subprocess.Popen([sys.executable, str(settings.ROOT / "pricewatch.py"), "run"], cwd=settings.ROOT, creationflags=flags,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"in_corso": True}


def post(path: str, body: dict):
    global _plan_active
    cfg = settings.load()
    if path == "/api/config":
        settings.save(settings.apply_update(cfg, body))
        if "intervallo_ore" in body.get("generale", {}) and plan_status(3)["attiva"]:
            schedule.enable(settings.load()["generale"]["intervallo_ore"])  # changes the times immediately
        return state()
    if path == "/api/schedule":
        if body.get("attiva"):
            schedule.enable(cfg["generale"].get("intervallo_ore", 3))
        else:
            schedule.disable()
        _plan_active = bool(body.get("attiva"))
        return state()
    if path == "/api/run":
        return start_run()
    if path == "/api/try":
        return try_title(body)
    if path == "/api/test-site":
        if body.get("canale"):
            return sitetest.test_channel(settings.clean_channel(body["canale"]), body.get("query") or "", cfg["generale"]["valuta"])
        site = next((s for s in catalog.site_list(cfg) if s["id"] == body.get("id")), None) or settings.clean_custom_site(body, cfg["generale"])
        result = sitetest.test_site(site, body.get("query") or "samsung ssd", home=cfg["generale"]["valuta"])
        if site.get("id") and any(s["id"] == site["id"] for s in catalog.site_list(cfg)):
            cfg["siti"].setdefault("esiti", {})[site["id"]] = result
            settings.save(cfg)
        return result
    if path == "/api/ebay-test":
        probe = {**cfg, "ebay": {**(cfg.get("ebay") or {}), **body}}
        market = ebay.marketplace(cfg["generale"]["paese"])
        if not market:
            return {"esito": "paese", "letti": 0}
        page, items = ebay.search(probe, "samsung ssd", market, limit=5)
        return {"esito": "ok" if page.ok else page.error, "letti": len(items), "esempio": items[0].title[:80] if items else ""}
    if path == "/api/telegram-test":
        probe = {**cfg, "notifiche": {**cfg["notifiche"], **body}}
        return {"esito": notify.send(probe, t(cfg, "tg.test"))}
    if path == "/api/telegram-id":
        probe = {**cfg, "notifiche": {**cfg["notifiche"], **body}}
        return {"ids": notify.chat_ids(probe)}
    raise KeyError(path)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _send(self, code: int, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, data):
        self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _local_host(self) -> bool:  # blocks sites that point one of their domains at 127.0.0.1
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self._local_host():
            return self._send(403, b"forbidden", "text/plain")
        path = self.path.split("?")[0]
        if path == "/":
            page = (GUI / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", TOKEN)
            return self._send(200, page.encode("utf-8"), TYPES[".html"])
        if path in ("/app.js", "/style.css"):
            return self._send(200, (GUI / path[1:]).read_bytes(), TYPES[Path(path).suffix])
        if path == "/report":
            report = settings.DATA / "report.html"
            return self._send(200, report.read_bytes(), TYPES[".html"]) if report.exists() else self._send(404, b"", "text/plain")
        if self.headers.get("X-PW-Token") != TOKEN:
            return self._send(403, b"forbidden", "text/plain")
        if path == "/api/state":
            return self._json(200, state())
        if path == "/api/ai":
            return self._json(200, ai.status())
        if path == "/api/run":
            return self._json(200, {**run_status(), "log": log_tail(), "report_data": _report_time()})
        return self._send(404, b"", "text/plain")

    def do_POST(self):
        if not self._local_host() or self.headers.get("X-PW-Token") != TOKEN:
            return self._send(403, b"forbidden", "text/plain")
        try:
            size = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(size) or b"{}")
            self._json(200, post(self.path, body))
        except (ValueError, RuntimeError, SystemExit, OSError) as e:
            self._json(400, {"errore": str(e)})
        except KeyError:
            self._send(404, b"", "text/plain")


def _report_time():
    report = settings.DATA / "report.html"
    return report.stat().st_mtime if report.exists() else None


def serve(port: int = 8771, open_browser: bool = True):
    server = None
    for candidate in range(port, port + 20):  # port in use: try the next one
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit("No free port")
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"PriceWatch: {url}")
    threading.Thread(target=rates.get, daemon=True).start()  # so the GUI already knows whether foreign sites are usable
    if open_browser:
        threading.Timer(0.4, webbrowser.open, [url]).start()
    server.serve_forever()
