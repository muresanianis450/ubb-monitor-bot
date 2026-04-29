import time
import requests
from playwright.sync_api import sync_playwright
import os


TARGET_URL = "https://academicinfo.ubbcluj.ro/ContracteStudii.aspx"
SEM_TARGET = "Sem:5 An:2025"
BLOCKED_MSG = "Nu se pot completa contracte"

CHECK_INTERVAL = 10  # ⚡ FAST MODE (10s)


# ─── TELEGRAM ─────────────────────────────
BOT_TOKEN = "8398873527:AAFAjI_iwIuCtliuBUDMNuB_pYe3gK5wU88"
CHAT_ID = "8244076992"


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def get_state(page):
    html = page.content().lower()

    options = page.locator("option").all_text_contents()
    found = any(SEM_TARGET.lower() in opt.lower() for opt in options)

    if not found:
        return "NOT_FOUND"

    if BLOCKED_MSG.lower() in html:
        return "CLOSED"

    return "OPEN"


def monitor(page):
    print("⚡ FAST monitor started")

    last_state = None
    alerted = False

    while True:
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)  # minimal delay

            state = get_state(page)

            print("STATE:", state)

            if state != last_state:
                last_state = state

                send_telegram(f"🔄 State changed → {state}")

            if state == "OPEN" and not alerted:
                send_telegram(f"🚨 UBB OPEN {SEM_TARGET}\n{TARGET_URL}")
                alerted = True

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        if os.path.exists("state.json"):
            context = browser.new_context(storage_state="state.json")
        else:
            context = browser.new_context()
        page = context.new_page()

        page.goto(TARGET_URL)

        send_telegram("🧠 Monitor started")

        monitor(page)


if __name__ == "__main__":
    main()
