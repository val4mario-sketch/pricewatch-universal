"""Notifications through a Telegram bot (free, arrives on the phone)."""
from __future__ import annotations

import os

import requests


def _creds(cfg: dict) -> tuple[str, str]:
    n = cfg.get("notifiche", {}) or {}
    token = os.environ.get("PW_TG_TOKEN") or (n.get("telegram_token") or "")
    chat = os.environ.get("PW_TG_CHAT") or str(n.get("telegram_chat_id") or "")
    return token.strip(), chat.strip()


def enabled(cfg: dict) -> bool:
    t, c = _creds(cfg)
    return bool(t and c)


def send(cfg: dict, text: str, silent: bool = False) -> str:
    token, chat = _creds(cfg)
    if not (token and chat):
        return "Telegram notifications are not configured"
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": text, "parse_mode": "HTML",
                                "disable_web_page_preview": "true",
                                "disable_notification": "true" if silent else "false"}, timeout=20)
        return "ok" if r.ok else f"Telegram error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Telegram error: {_hide(e, token)}"


def send_document(cfg: dict, path: str, filename: str, caption: str = "", silent: bool = True) -> str:
    token, chat = _creds(cfg)
    if not (token and chat):
        return "Telegram notifications are not configured"
    try:
        with open(path, "rb") as fh:
            r = requests.post(f"https://api.telegram.org/bot{token}/sendDocument",
                              data={"chat_id": chat, "caption": caption,
                                    "disable_notification": "true" if silent else "false"},
                              files={"document": (filename, fh, "text/html")}, timeout=60)
        return "ok" if r.ok else f"Telegram error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Telegram error: {_hide(e, token)}"


def _hide(e: Exception, token: str) -> str:
    # requests' network errors include the URL, which contains the token: it would end up in the log
    return str(e).replace(token, "***")


def chat_ids(cfg: dict) -> list[str]:
    token, _ = _creds(cfg)
    if not token:
        raise SystemExit("Enter telegram_token in config.yaml first (or PW_TG_TOKEN).")
    r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=20)
    r.raise_for_status()
    ids = []
    for u in r.json().get("result", []):
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat", {})
        if chat.get("id") is not None:
            ids.append(f"{chat['id']}  ({chat.get('first_name') or chat.get('title') or ''})")
    return sorted(set(ids))
