#!/bin/sh
# Avvio su macOS e Linux
cd "$(dirname "$0")" || exit 1
python3 -c "import yaml,bs4,lxml,requests,playwright" 2>/dev/null || python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
exec python3 pricewatch.py gui
