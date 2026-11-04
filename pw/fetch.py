"""Download delle pagine con pause per dominio, impronta browser e fallback Playwright."""
from __future__ import annotations

import json
import os
import random
import re
import signal
import subprocess
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

try:  # impersona l'impronta TLS/HTTP2 di Chrome: passa molti più controlli anti-bot
    from curl_cffi import requests as cffi_requests
except Exception:  # pragma: no cover
    cffi_requests = None

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
    "Cache-Control": "no-cache",
}
BLOCK_MARKERS = ("cf-chl", "challenge-platform", "captcha-delivery", "px-captcha", "/errors/validatecaptcha",
                 "robot check", "are you a robot", "sei un robot", "unusual traffic", "access denied",
                 "pardon our interruption", "attention required", "just a moment...", "datadome")


BROWSER_EXTRA_SEC = 25  # oltre al caricamento: attesa, scorrimento e chiusura


def _kill_tree(proc: subprocess.Popen):
    """Chiude anche Chromium, non solo il processo che lo ha avviato."""
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, creationflags=0x08000000)
    else:
        os.killpg(proc.pid, signal.SIGKILL)
    proc.communicate()


@dataclass
class Page:
    url: str
    status: int
    html: str
    error: str = ""
    blocked: bool = False
    via: str = ""

    @property
    def ok(self) -> bool:
        return self.status == 200 and not self.blocked and not self.error


# Il sito ha mandato a una pagina di accesso o di verifica anti-bot: non si prova ad aggirarla.
_WALL_URL = re.compile(r"/login|passport\.|/signin|/verify/|/punish|region-ban", re.I)


def looks_blocked(status: int, html: str, url: str = "") -> bool:
    if status in (401, 403, 429, 503):
        return True
    parts = urlparse(url)
    if _WALL_URL.search(parts.netloc + parts.path):
        return True
    head = (html or "")[:40000].lower()
    if len(html or "") < 60000 and any(m in head for m in BLOCK_MARKERS):
        return True
    return False


class Fetcher:
    def __init__(self, cfg: dict):
        g = cfg.get("generale", {})
        self.headers = {**HEADERS, "Accept-Language": g.get("accept_language") or HEADERS["Accept-Language"]}
        self.dmin = float(g.get("pausa_min_sec", 3))
        self.dmax = float(g.get("pausa_max_sec", 6))
        self.timeout = float(g.get("timeout_sec", 25))
        self.use_cffi = bool(g.get("impersona_browser", True)) and cffi_requests is not None
        self.headless = bool(g.get("playwright_headless", True))
        self._last: dict[str, float] = {}
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._session = requests.Session()
        self._session.headers.update(self.headers)

    def _pause(self, host: str):
        last = self._last.get(host)
        if last is not None:
            wait = random.uniform(self.dmin, self.dmax) - (time.time() - last)
            if wait > 0:
                time.sleep(wait)

    def get(self, url: str, browser: bool = False) -> Page:
        host = urlparse(url).netloc
        with self._locks[host]:
            self._pause(host)
            try:
                page = self._get_browser(url) if browser else self._get_http(url)
            finally:
                self._last[host] = time.time()
        return page

    def _get_http(self, url: str) -> Page:
        try:
            if self.use_cffi:
                r = cffi_requests.get(url, headers=self.headers, impersonate="chrome", timeout=self.timeout,
                                      allow_redirects=True)
                via = "curl_cffi"
            else:
                r = self._session.get(url, timeout=self.timeout, allow_redirects=True)
                via = "requests"
            html = r.text or ""
            return Page(str(r.url), r.status_code, html, blocked=looks_blocked(r.status_code, html, str(r.url)), via=via)
        except Exception as e:  # rete, timeout, TLS…
            return Page(url, 0, "", error=f"{type(e).__name__}: {e}"[:200])

    # ----------------------------------------------------------- Playwright
    @staticmethod
    def browser_available() -> bool:
        try:
            import playwright.sync_api  # noqa: F401
            return True
        except Exception:
            return False

    def _get_browser(self, url: str) -> Page:
        goto_ms = int(self.timeout * 1000) + 20000
        limit = goto_ms / 1000 + BROWSER_EXTRA_SEC
        cmd = [sys.executable, str(Path(__file__).with_name("browser_page.py")), url, UA, str(goto_ms), "1" if self.headless else "0"]
        windows = sys.platform == "win32"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000 if windows else 0,
                                start_new_session=not windows)
        try:
            out, err = proc.communicate(timeout=limit)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            return Page(url, 0, "", error=f"Browser: no answer after {limit:.0f} s")
        if proc.returncode != 0:
            lines = err.decode("utf-8", "replace").strip().splitlines()
            return Page(url, 0, "", error=f"Browser: {lines[-1] if lines else proc.returncode}"[:200])
        try:
            data = json.loads(out)
        except ValueError:
            return Page(url, 0, "", error="Browser: unreadable answer")
        return Page(data["url"], data["status"], data["html"], blocked=looks_blocked(data["status"], data["html"], data["url"]), via="playwright")

    def close(self):
        pass
