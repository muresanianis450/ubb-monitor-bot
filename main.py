import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from playwright.sync_api import sync_playwright

# ─── ENV CONFIG ────────────────────────────────────────────────
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

NOTIFY_EMAILS = os.getenv("NOTIFY_EMAILS", "").split(",")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "15"))

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
SESSION_DIR = os.getenv("SESSION_DIR", "/tmp/user_data")
os.makedirs(SESSION_DIR, exist_ok=True)

IS_CLOUD = os.getenv("CLOUD", "false") == "true"

TARGET_URL = "https://academicinfo.ubbcluj.ro/ContracteStudii.aspx"
SEM_TARGET = "Sem:5 An:2025"
BLOCKED_MSG = "Nu se pot completa contracte"
# ───────────────────────────────────────────────────────────────


def send_email(subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("⚠️ Email not configured")
        return

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = ", ".join(NOTIFY_EMAILS)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, NOTIFY_EMAILS, msg.as_string())

    print("📧 Email sent:", subject)


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

            print(f"📊 State: {state}")

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

                    send_email(
                        f"🚨 UBB OPEN {SEM_TARGET}",
                        f"{SEM_TARGET} is OPEN at {now}\n{TARGET_URL}"
                    )

                    alerted_open = True

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(10)


def main():
    with sync_playwright() as p:

        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=IS_CLOUD
        )

        page = context.new_page()
        page.goto(TARGET_URL)

        print("💾 Browser started")

        send_email(
            "🧠 Monitor started",
            f"Watching {SEM_TARGET}\n{TARGET_URL}"
        )

        monitor(page)


if __name__ == "__main__":
    main()
