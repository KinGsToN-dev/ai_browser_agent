import logging
from playwright.sync_api import sync_playwright

log = logging.getLogger("browser_manager")

class BrowserManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BrowserManager, cls).__new__(cls)
            cls._instance._pw = None
            cls._instance.browser = None
        return cls._instance

    def connect(self, cdp_url="http://localhost:9222"):
        if self._pw is None:
            log.info("Инициализация Playwright и подключение к CDP...")
            self._pw = sync_playwright().start()
            self.browser = self._pw.chromium.connect_over_cdp(cdp_url)
        return self.browser

    def get_page_by_domain(self, domain: str):
        self.connect()
        for ctx in self.browser.contexts:
            for page in ctx.pages:
                if domain in page.url:
                    return page
        return None

    def close(self):
        if self._pw:
            log.info("Закрываю Playwright...")
            self._pw.stop()
            self._pw = None
            self.browser = None
