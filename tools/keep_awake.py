"""Opens the study app in a headless browser so Streamlit doesn't put it to sleep.

Run by GitHub Actions every few hours (.github/workflows/keep-awake.yml).
It only LOOKS at the first page: it never ticks the consent box, so it never
creates a participant file. If the app is asleep, it clicks the wake-up button.
"""

import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://gamestudy.streamlit.app/"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, timeout=90_000)
    page.wait_for_timeout(15_000)
    # Streamlit's sleep page has a button like "Yes, get this app back up!"
    wake = page.get_by_role("button", name="get this app back up")
    if wake.count():
        print("App was asleep -> waking it up")
        wake.first.click()
        page.wait_for_timeout(90_000)  # give it time to start
    else:
        print("App is awake")
    browser.close()
