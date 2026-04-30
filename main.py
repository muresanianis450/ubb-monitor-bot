import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load .env
load_dotenv()

# ─── CONFIG ────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 15))
TARGET_URL = os.getenv("TARGET_URL")
SEM_TARGET = os.getenv("SEM_TARGET")
BLOCKED_MSG = os.getenv("BLOCKED_MSG")
# ───────────────────────────────────────────────────────────


def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data = {
            "chat_id": CHAT_ID,
            "text": message
        }

        requests.post(url, data=data, timeout=10)
        print("📲 Telegram sent")

    except Exception as e:
        print("❌ Telegram failed:", e)


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
    print("👀 Monitoring started...")

    last_state = None
    alerted_open = False

    while True:
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            state = get_state(page)

            print(f"📊 State: {state} | URL: {page.url}")

            if state != last_state:
                print(f"🔄 State changed: {last_state} → {state}")
                last_state = state

            if state == "NOT_FOUND":
                print("❌ Semester not visible yet")

            elif state == "CLOSED":
                print("🔴 Still closed")
                alerted_open = False

            elif state == "OPEN":
                print("🟢 OPEN!!!")

                if not alerted_open:
                    now = datetime.now().strftime("%H:%M:%S")

                    send_telegram(
                        f"🚨 UBB OPEN {SEM_TARGET}\n🕒 {now}\n{TARGET_URL}"
                    )

                    alerted_open = True

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(10)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            storage_state="state.json"
        )

        page = context.new_page()
        page.goto(TARGET_URL)

        print("💾 Session loaded. Starting monitor...")

        send_telegram(
            f"🧠 Monitor started\nWatching {SEM_TARGET}\n{TARGET_URL}"
        )

        monitor(page)


if __name__ == "__main__":
    main()
