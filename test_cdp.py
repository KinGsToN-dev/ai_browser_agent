from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    print("Контекстов:", len(browser.contexts))
    for ctx in browser.contexts:
        for page in ctx.pages:
            print("Вкладка:", page.url[:100])
    browser.close()