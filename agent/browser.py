# agent/browser.py
import time
import logging
from playwright.sync_api import sync_playwright

log = logging.getLogger("browser")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class BrowserAgent:
    def __init__(self, cdp_url="http://localhost:9222"):
        self.cdp_url = cdp_url
        self._pw = None
        self.browser = None
        self.page = None
        self._connect()

    def _connect(self):
        log.info("Подключаюсь к CDP...")
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.connect_over_cdp(self.cdp_url)
        
        # Ищем вкладку ChatGPT
        target_page = None
        for ctx in self.browser.contexts:
            for page in ctx.pages:
                if "chatgpt.com" in page.url:
                    target_page = page
                    break
            if target_page:
                break

        if not target_page:
            raise RuntimeError("Вкладка ChatGPT не найдена! Открой chatgpt.com в Chrome агента.")

        self.page = target_page
        self.page.bring_to_front()
        log.info(f"Прицепился к вкладке: {self.page.url}")

    def send(self, text: str):
        log.info(f"Отправляю промпт ({len(text)} символов)...")
        
        # 1. Кликаем в поле ввода (ProseMirror)
        input_box = self.page.locator('div[contenteditable="true"]').first
        input_box.click()
        time.sleep(0.2) # небольшая пауза для фокуса

        # 2. Очищаем поле (на всякий случай, если там остался старый текст)
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        time.sleep(0.2)

        # 3. Печатаем текст посимвольно (чтобы ProseMirror корректно обработал)
        # Для длинных текстов это может быть медленно. Если нужно быстро — можно вставить через clipboard.
        self.page.keyboard.insert_text(text)
        time.sleep(0.5) # даем время на рендер текста в поле

        # 4. Нажимаем Enter для отправки
        self.page.keyboard.press("Enter")
        log.info("Промпт отправлен (нажат Enter).")

    def wait_answer(self, timeout_sec=240, stable_sec=2.0):
        log.info("Жду ответа от ChatGPT...")
        start_time = time.time()
        last_text = ""
        stable_start = None

        # Цепочка селекторов: от самого точного к самому общему
        # 1. data-message-author-role="assistant" — если есть
        # 2. .DilRenderer — новый класс рендерера ответа
        # 3. [data-message-id] — любой блок с ID сообщения (запасной)
        SELECTORS = [
            '[data-message-author-role="assistant"]',
            '.DilRenderer-tB76Jj',
            '[data-dil-message-id]',
        ]

        while time.time() - start_time < timeout_sec:
            current_text = ""
            for sel in SELECTORS:
                loc = self.page.locator(sel)
                if loc.count() > 0:
                    current_text = loc.last.inner_text()
                    break

            if current_text and current_text == last_text:
                if stable_start is None:
                    stable_start = time.time()
                elif time.time() - stable_start >= stable_sec:
                    log.info(f"Ответ получен ({len(current_text)} символов).")
                    return current_text
            else:
                last_text = current_text
                stable_start = None

            time.sleep(0.3)

        raise TimeoutError(f"ChatGPT не ответил за {timeout_sec} секунд.")
    def close(self):
        if self._pw:
            self._pw.stop()

if __name__ == "__main__":
    # Тестовый запуск
    agent = BrowserAgent()
    try:
        agent.send("Привет! Напиши ровно одно слово: 'Тест'")
        answer = agent.wait_answer()
        print("\n=== ОТВЕТ CHATGPT ===")
        print(answer)
        print("=====================")
    finally:
        agent.close()