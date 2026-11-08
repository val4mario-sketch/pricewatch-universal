"""Price history in SQLite."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, sources TEXT
);
CREATE TABLE IF NOT EXISTS offers(
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER NOT NULL, ts TEXT NOT NULL,
  component TEXT NOT NULL, model TEXT, level TEXT, title TEXT, price REAL, shipping REAL,
  total REAL, shop TEXT, source TEXT, url TEXT, warnings TEXT, tags TEXT, extra TEXT
);
CREATE INDEX IF NOT EXISTS ix_offers_run ON offers(run_id);
CREATE TABLE IF NOT EXISTS notified(key TEXT PRIMARY KEY, ts TEXT);
CREATE TABLE IF NOT EXISTS pending(key TEXT PRIMARY KEY, why TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS discarded(run_id INTEGER, component TEXT, title TEXT, price REAL, source TEXT, reason TEXT, score INTEGER);
CREATE INDEX IF NOT EXISTS ix_discarded_run ON discarded(run_id);
CREATE TABLE IF NOT EXISTS ai_cache(key TEXT PRIMARY KEY, answer TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS best(run_id INTEGER, ts TEXT, component TEXT, total REAL, PRIMARY KEY(run_id, component));
"""


class Store:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def new_run(self) -> int:
        cur = self.db.execute("INSERT INTO runs(ts) VALUES(?)", (datetime.now().isoformat(timespec="seconds"),))
        self.db.commit()
        return cur.lastrowid

    def finish_run(self, run_id: int, sources: dict):
        self.db.execute("UPDATE runs SET sources=? WHERE id=?", (json.dumps(sources, ensure_ascii=False), run_id))
        self.db.commit()

    def add_offers(self, run_id: int, offers: list[dict]):
        ts = datetime.now().isoformat(timespec="seconds")
        self.db.executemany(
            "INSERT INTO offers(run_id,ts,component,model,level,title,price,shipping,total,shop,source,url,"
            "warnings,tags,extra) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [(run_id, ts, o["component"], o["model"], o["level"], o["title"], o["price"], o["shipping"],
              o["total"], o["shop"], o["source"], o["url"], json.dumps(o["warnings"], ensure_ascii=False),
              json.dumps(o["tags"], ensure_ascii=False), json.dumps(o.get("extra", {}), ensure_ascii=False))
             for o in offers])
        self.db.commit()

    def last_run(self):
        # a run with no offers (usually no connection) does not replace the last successful one
        return self.db.execute("SELECT * FROM runs WHERE sources IS NOT NULL AND id IN (SELECT run_id FROM offers) "
                               "ORDER BY id DESC LIMIT 1").fetchone()

    def offers_of_run(self, run_id: int) -> list[dict]:
        rows = self.db.execute("SELECT * FROM offers WHERE run_id=? ORDER BY total", (run_id,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            for k in ("warnings", "tags", "extra"):
                d[k] = json.loads(d[k] or ("{}" if k == "extra" else "[]"))
            out.append(d)
        return out

    def min_before(self, component: str, run_id: int) -> float | None:
        r = self.db.execute("SELECT MIN(total) FROM best WHERE component=? AND run_id<?", (component, run_id)).fetchone()
        return r[0]

    def add_best(self, run_id: int, totals: dict[str, float]):
        ts = datetime.now().isoformat(timespec="seconds")
        self.db.executemany("INSERT OR REPLACE INTO best VALUES(?,?,?,?)", [(run_id, ts, c, v) for c, v in totals.items()])
        self.db.commit()

    def daily_min(self, component: str, days: int = 90) -> list[tuple[str, float]]:
        rows = self.db.execute(
            "SELECT substr(ts,1,10) d, MIN(total) FROM best WHERE component=? "
            "AND ts >= date('now', ?) GROUP BY d ORDER BY d", (component, f"-{days} days")).fetchall()
        return [(r[0], r[1]) for r in rows]

    def prune(self, keep_days: int = 60):
        """Keeps recent offers. The lows in `best` remain: they are enough for history and alerts."""
        limit = (datetime.now() - timedelta(days=keep_days)).isoformat(timespec="seconds")
        self.db.execute("DELETE FROM offers WHERE ts < ?", (limit,))
        self.db.commit()

    def add_discarded(self, run_id: int, rows: list[dict], per_product: int = 1000):
        """Discarded offers with the reason, closest to what is wanted first. Only the latest runs are needed."""
        counts: dict[str, int] = {}
        keep = []
        for r in sorted(rows, key=lambda x: -x.get("score", 0)):
            counts[r["component"]] = counts.get(r["component"], 0) + 1
            if counts[r["component"]] <= per_product:
                keep.append((run_id, r["component"], r["title"], r.get("price"), r.get("source"), r.get("reason"), r.get("score", 0)))
        self.db.executemany("INSERT INTO discarded VALUES(?,?,?,?,?,?,?)", keep)
        self.db.execute("DELETE FROM discarded WHERE run_id NOT IN (SELECT id FROM runs ORDER BY id DESC LIMIT 3)")
        self.db.commit()

    def discarded_of_run(self, run_id: int, component: str, limit: int = 40) -> tuple[int, list[dict]]:
        n = self.db.execute("SELECT COUNT(*) FROM discarded WHERE run_id=? AND component=?", (run_id, component)).fetchone()[0]
        rows = self.db.execute("SELECT * FROM discarded WHERE run_id=? AND component=? ORDER BY score DESC, price LIMIT ?", (run_id, component, limit)).fetchall()
        return n, [dict(r) for r in rows]

    def ai_get(self, key: str) -> dict | None:
        r = self.db.execute("SELECT answer FROM ai_cache WHERE key=?", (key,)).fetchone()
        return json.loads(r[0]) if r else None

    def ai_put(self, key: str, answer: dict):
        self.db.execute("INSERT OR REPLACE INTO ai_cache VALUES(?,?,?)", (key, json.dumps(answer), datetime.now().isoformat(timespec="seconds")))
        self.db.commit()

    def was_notified(self, key: str) -> bool:
        return self.db.execute("SELECT 1 FROM notified WHERE key=?", (key,)).fetchone() is not None

    def mark_notified(self, key: str):
        self.db.execute("INSERT OR IGNORE INTO notified VALUES(?,?)", (key, datetime.now().isoformat(timespec="seconds")))
        self.db.execute("DELETE FROM pending WHERE key=?", (key,))
        self.db.commit()

    def pending_why(self, key: str) -> str | None:
        r = self.db.execute("SELECT why FROM pending WHERE key=?", (key,)).fetchone()
        return r[0] if r else None

    def mark_pending(self, key: str, why: str):
        self.db.execute("INSERT OR REPLACE INTO pending VALUES(?,?,?)", (key, why, datetime.now().isoformat(timespec="seconds")))
        self.db.commit()
