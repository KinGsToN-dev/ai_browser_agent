import time
import logging
from .base import BaseProvider
from agent.browser_manager import BrowserManager

log = logging.getLogger("provider.deepseek")

class DeepSeekProvider(BaseProvider):
    def __init__(self):
        self.manager = BrowserManager()
        self.page = None
        self.connect()

    def connect(self):
        log.info("Подключаюсь к вкладке DeepSeek...")
        self.page = self.manager.get_page_by_domain("chat.deepseek.com")
        if not self.page:
            raise RuntimeError("Вкладка DeepSeek не найдена!")
        self.page.bring_to_front()
        log.info(f"Прицепился к вкладке: {self.page.url}")

    def send(self, text: str):
        log.info(f"Отправляю промпт ({len(text)} символов)...")
        self.page.bring_to_front()
        input_box = self.page.locator('textarea').first
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
        log.info("Жду ответа от DeepSeek...")
        start_time = time.time()
        last_text = ""
        stable_start = None
        SELECTORS = ['.ds-markdown', '[class*="message"] .markdown', '[class*="chat-message"]']
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
        raise TimeoutError("DeepSeek не ответил.")

    def check_limit(self) -> bool:
        # Ищем НЕ текст сообщений, а системные плашки об ошибке
        try:
            # 1. Ищем красные уведомления (обычно они содержат слово limit или rate)
            error_toast = self.page.locator('.error, .toast, [class*="error"], [class*="alert"]')
            if error_toast.count() > 0:
                toast_text = error_toast.first.inner_text().lower()
                if "limit" in toast_text or "лимит" in toast_text or "rate" in toast_text:
                    return True
            
            # 2. Проверяем, не заблокирована ли кнопка отправки
            send_btn = self.page.locator('button[type="submit"]').first
            if send_btn.count() > 0 and send_btn.is_disabled():
                # Если кнопка неактивна, но поле ввода пустое — возможно, лимит
                pass 
                
            return False
        except Exception:
            return False

    def start_new_chat(self):
        log.info("Создаю новый чат в DeepSeek...")
        try:
            btn = self.page.locator('button:has-text("New chat"), a[href="/"]').first
            if btn.count() > 0:
                btn.click()
                time.sleep(2)
            else:
                self.page.goto("https://chat.deepseek.com/")
                time.sleep(2)
        except Exception as e:
            log.error(f"Не удалось создать новый чат: {e}")

    def close(self):
        pass
