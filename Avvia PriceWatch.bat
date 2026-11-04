@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python non trovato / Python not found: https://www.python.org/downloads/
  pause
  exit /b 1
)
python -c "import yaml,bs4,lxml,requests,playwright" >nul 2>nul
if errorlevel 1 python -m pip install -r requirements.txt
python -m playwright install chromium
python pricewatch.py gui
pause
