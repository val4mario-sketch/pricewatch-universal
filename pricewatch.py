#!/usr/bin/env python3
"""PriceWatch Universale: controlla i prezzi dei prodotti scelti nella GUI.

Comandi:
  python pricewatch.py              apre la GUI
  python pricewatch.py gui [--porta N] [--senza-browser]
  python pricewatch.py run [--prodotto ID]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from pw import notify, report, runner, server, settings  # noqa: E402
from pw.i18n import t  # noqa: E402
from pw.store import Store  # noqa: E402

LOG_LIMIT = 2_000_000


def _open_log():
    """Il giro scrive nel log, anche senza console (pythonw.exe dall'Utilità di pianificazione)."""
    settings.DATA.mkdir(parents=True, exist_ok=True)
    path = settings.DATA / "pricewatch.log"
    mode = "w" if path.exists() and path.stat().st_size > LOG_LIMIT else "a"
    log = open(path, mode, encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = log


def _acquire_lock() -> Path | None:
    """Un giro alla volta. Un blocco più vecchio del limite dell'attività (2 ore) è rimasto da un crash."""
    lock = settings.DATA / "run.lock"
    if lock.exists() and time.time() - lock.stat().st_mtime > 2 * 3600:
        lock.unlink()
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        return lock
    except FileExistsError:
        return None


def send_summary(cfg, store, report_path):
    # di notte il riepilogo arriva senza suono; gli avvisi di prezzo suonano sempre
    now = datetime.now()
    silent = now.hour >= 23 or now.hour < 8
    print("summary:", notify.send(cfg, report.telegram_summary(cfg, store), silent=silent))
    print("report file:", notify.send_document(cfg, report_path, f"pricewatch-{now:%Y-%m-%d-%H%M}.html", t(cfg, "tg.file")))


def cmd_run(a):
    _open_log()
    lock = _acquire_lock()
    if lock is None:
        print("Another run is in progress.")
        return
    try:
        cfg = settings.load()
        if not any(p.get("attivo", True) for p in cfg.get("prodotti", [])):
            print("No products to check.")
            return
        store = Store(str(settings.DATA / "pricewatch.db"))
        run_id = runner.run(cfg, store, only_product=a.prodotto)
        if not store.offers_of_run(run_id):
            print("No offers read (no connection?): the last good report stays in place.")
            return
        out = report.generate(cfg, store, str(settings.DATA / "report.html"))
        print(f"Report: {out}")
        if not a.prodotto and cfg.get("notifiche", {}).get("riepilogo", True) and notify.enabled(cfg):
            send_summary(cfg, store, out)
        if cfg.get("generale", {}).get("apri_report"):
            webbrowser.open(Path(out).as_uri())
    finally:
        lock.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description="PriceWatch Universale")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("gui")
    p.add_argument("--porta", type=int, default=8771)
    p.add_argument("--senza-browser", action="store_true")
    p = sub.add_parser("run")
    p.add_argument("--prodotto")
    a = ap.parse_args()
    if a.cmd == "run":
        cmd_run(a)
    else:
        server.serve(getattr(a, "porta", 8771), not getattr(a, "senza_browser", False))


if __name__ == "__main__":
    main()
