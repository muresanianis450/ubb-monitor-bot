import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from playwright.sync_api import sync_playwright

# ─── CONFIG ────────────────────────────────────────────────
CONFIG = {
    "gmail_address": "muresanianis450@gmail.com",
    "gmail_app_password": "zqax qiip hinc jjnb",
    "notify_email": [
        "muresanianis450@gmail.com",
        "andreeajigarov@gmail.com",
    ],
    "check_interval": 15,
}

TARGET_URL = "https://academicinfo.ubbcluj.ro/ContracteStudii.aspx"
SEM_TARGET = "Sem:5 An:2025"
BLOCKED_MSG = "Nu se pot completa contracte"
SESSION_DIR = "./user_data"
# ───────────────────────────────────────────────────────────


def send_email(subject, body):
    recipients = CONFIG["notify_email"]

    msg = MIMEMultipart()
    msg["From"] = CONFIG["gmail_address"]
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(CONFIG["gmail_address"], CONFIG["gmail_app_password"])
        server.sendmail(CONFIG["gmail_address"], recipients, msg.as_string())

    print("📧 Email sent:", subject)


def get_state(page):
    """
    Returns:
        ("OPEN" | "CLOSED" | "NOT_FOUND")
    """

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

            # ─── STATE CHANGE DETECTION ───
            if state != last_state:
                print(f"🔄 State changed: {last_state} → {state}")
                last_state = state

            # ─── LOGIC ───
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

            time.sleep(CONFIG["check_interval"])

        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(10)


def main():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False
        )

        page = context.new_page()
        page.goto(TARGET_URL)

        print("""
🧠 FIRST TIME SETUP:
1. Log in manually
2. Solve CAPTCHA
3. Navigate to semesters page
4. Press ENTER here
""")

        input()

        print("💾 Session active. Starting monitor...")

        # optional startup email
        send_email(
            "🧠 Monitor started",
            f"Watching {SEM_TARGET}\n{TARGET_URL}"
        )

        monitor(page)


if __name__ == "__main__":
    main()
