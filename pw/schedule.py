"""Automatic start every N hours, at fixed times from midnight. With the PC off the run is skipped and restarts at the next one."""
from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_NAME = os.environ.get("PW_TASK_NAME", "PriceWatch Universale")
CRON_MARK = "# " + re.sub(r"\W+", "-", TASK_NAME.lower())
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def hours_of_day(every: int) -> list[int]:
    return list(range(0, 24, every))


def next_run(every: int, now: datetime | None = None) -> datetime:
    now = now or datetime.now()
    for h in hours_of_day(every):
        when = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if when > now:
            return when
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


def _ps(script: str) -> subprocess.CompletedProcess:
    encoded = base64.b64encode(("$ErrorActionPreference='Stop';" + script).encode("utf-16-le")).decode()
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                          capture_output=True, text=True, timeout=60, creationflags=_NO_WINDOW)


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _pythonw() -> str:
    exe = Path(sys.executable)
    windowless = exe.with_name("pythonw.exe")
    return str(windowless if windowless.exists() else exe)


def _crontab_read() -> list[str]:
    r = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return r.stdout.splitlines() if r.returncode == 0 else []


def _crontab_write(lines: list[str]):
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True)


def cron_line(every: int) -> str:
    hours = ",".join(str(h) for h in hours_of_day(every))
    return f'0 {hours} * * * cd "{ROOT}" && "{sys.executable}" pricewatch.py run {CRON_MARK}'


def enable(every: int) -> dict:
    every = int(every)
    if not 1 <= every <= 24:
        raise ValueError("every must be between 1 and 24 hours")
    if os.name == "nt":
        triggers = ",".join(f"(New-ScheduledTaskTrigger -Daily -At '{h:02d}:00')" for h in hours_of_day(every))
        script = (
            f"$a=New-ScheduledTaskAction -Execute {_quote(_pythonw())} -Argument 'pricewatch.py run' -WorkingDirectory {_quote(str(ROOT))};"
            f"$t=@({triggers});"
            "$s=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries "
            "-ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew;"
            "$s.StartWhenAvailable=$false;"
            f"Register-ScheduledTask -TaskName {_quote(TASK_NAME)} -Action $a -Trigger $t -Settings $s -Force | Out-Null"
        )
        r = _ps(script)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip()[:400])
    else:
        if not shutil.which("crontab"):
            raise RuntimeError("crontab not found")
        _crontab_write([x for x in _crontab_read() if CRON_MARK not in x] + [cron_line(every)])
    return status(every)


def disable() -> dict:
    if os.name == "nt":
        if _exists_windows():
            r = _ps(f"Unregister-ScheduledTask -TaskName {_quote(TASK_NAME)} -Confirm:$false")
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip()[:400])
    elif shutil.which("crontab"):
        _crontab_write([x for x in _crontab_read() if CRON_MARK not in x])
    return {"attiva": False}


def _exists_windows() -> bool:
    return _ps(f"Get-ScheduledTask -TaskName {_quote(TASK_NAME)} | Out-Null").returncode == 0


def status(every: int | None = None) -> dict:
    if os.name == "nt":
        active = _exists_windows()
    else:
        active = shutil.which("crontab") is not None and any(CRON_MARK in x for x in _crontab_read())
    result = {"attiva": active}
    if active and every:
        result["prossimo"] = next_run(int(every)).isoformat(timespec="minutes")
    return result
