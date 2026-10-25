import time
import logging
from .base import BaseProvider
from agent.browser_manager import BrowserManager

log = logging.getLogger("provider.chatgpt")

class ChatGPTProvider(BaseProvider):
    def __init__(self):
        self.manager = BrowserManager()
        self.page = None
        self.connect()

    def connect(self):
        log.info("Подключаюсь к вкладке ChatGPT...")
        self.page = self.manager.get_page_by_domain("chatgpt.com")
        if not self.page:
            raise RuntimeError("Вкладка ChatGPT не найдена!")
        self.page.bring_to_front()
        log.info(f"Прицепился к вкладке: {self.page.url}")

    def send(self, text: str):
        log.info(f"Отправляю промпт ({len(text)} символов)...")
        self.page.bring_to_front()
        input_box = self.page.locator('div[contenteditable="true"]').first
        input_box.wait_for(state="visible", timeout=15000)
        input_box.click()
        time.sleep(0.2)
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        time.sleep(0.2)
        self.page.keyboard.insert_text(text)
        time.sleep(0.5)
        self.page.keyboard.press("Enter")
        log.info("Промпт отправлен.")

    def wait_answer(self, timeout_sec=240, stable_sec=2.0) -> str:
        log.info("Жду ответа от ChatGPT...")
        start_time = time.time()
        last_text = ""
        stable_start = None
        SELECTORS = ['[data-message-author-role="assistant"]', '.DilRenderer-tB76Jj', '[data-dil-message-id]']
        while time.time() - start_time < timeout_sec:
            current_text = ""
            for sel in SELECTORS:
                loc = self.page.locator(sel)
                if loc.count() > 0:
                    current_text = loc.last.inner_text()
                    break
            if current_text and current_text == last_text:
                if stable_start is None: stable_start = time.time()
                elif time.time() - stable_start >= stable_sec:
                    return current_text
            else:
                last_text = current_text
                stable_start = None
            time.sleep(0.3)
        raise TimeoutError("ChatGPT не ответил.")

    def check_limit(self) -> bool:
        # ВРЕМЕННО ДЛЯ ТЕСТА: всегда True
        return True 
        # В будущем:
        # page_text = self.page.locator("body").inner_text().lower()
        # return "limit" in page_text or "лимит" in page_text

    def start_new_chat(self):
        log.info("Создаю новый чат в ChatGPT...")
        try:
            btn = self.page.locator('a[href="/"], button[aria-label*="New chat"]').first
            if btn.count() > 0:
                btn.click()
                time.sleep(2)
            else:
                self.page.goto("https://chatgpt.com/")
                time.sleep(2)
        except Exception as e:
            log.error(f"Не удалось создать новый чат: {e}")

    def close(self):
        # НЕ закрываем менеджер, он общий!
        pass
