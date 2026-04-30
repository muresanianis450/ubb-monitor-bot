from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="./session",
        headless=False  # so you can see and interact
    )
    page = context.new_page()
    page.goto("https://academicinfo.ubbcluj.ro/ContracteStudii.aspx")

    input("Log in manually in the browser, solve CAPTCHA, then press Enter here...")

    context.storage_state(path="session_state.json")
    print("✅ Session saved to session_state.json")
    context.close()