"""Opens a page with the invisible browser and writes the result as JSON. Runs in a separate process: if the page
hangs, fetch.py closes it when time runs out and the run continues."""
import json
import sys

from playwright.sync_api import sync_playwright


def main(url: str, user_agent: str, goto_ms: int, headless: bool):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_context(user_agent=user_agent, viewport={"width": 1366, "height": 900}).new_page()
        resp = page.goto(url, timeout=goto_ms, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        for _ in range(3):  # scrolls to load "lazy" results
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(700)
        sys.stdout.write(json.dumps({"url": page.url, "status": resp.status if resp else 200, "html": page.content()}))
        sys.stdout.flush()
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4] == "1")
