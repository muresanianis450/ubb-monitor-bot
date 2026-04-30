from playwright.sync_api import sync_playwright

TARGET_URL = "https://academicinfo.ubbcluj.ro/ContracteStudii.aspx"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # visible browser
    context = browser.new_context()
    page = context.new_page()

    page.goto(TARGET_URL)

    print("""
1. Log in
2. Solve CAPTCHA
3. Navigate to the page where Sem:5 is visible
4. Press ENTER here
""")

    input()

    # 💾 SAVE SESSION
    context.storage_state(path="state.json")

    print("✅ state.json saved!")

    browser.close()
