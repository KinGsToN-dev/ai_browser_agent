# AI Browser Agent (Mini-Claude)

Автономный ИИ-агент на базе Playwright и CDP (Chrome DevTools Protocol). 
Управляет веб-интерфейсами LLM (ChatGPT, DeepSeek), пишет код, запускает тесты и исправляет ошибки.

## 🚀 Основные возможности

- **Автономность:** Агент работает в цикле, вызывая инструменты (`read_file`, `write_file`, `run`).
- **Самокоррекция:** Видит вывод `pytest`, находит ошибки и исправляет код.
- **Мультипровайдерность:** Поддержка ChatGPT и DeepSeek.
- **Fallback-логика:** При исчерпании лимита в ChatGPT автоматически переключается на DeepSeek, передавая контекст.
- **Защита от циклов:** Если агент пытается сделать одно и то же действие дважды, он получает «пинок» и меняет стратегию.
- **Устойчивый парсер:** Извлекает JSON даже из «грязного» ответа LLM.

## 🛠 Установка

1. Установите зависимости:
   ```bash
   pip install playwright pytest
   playwright install chromium
Запустите Chrome в режиме отладки (CDP):

powershell
.\start_chrome.ps1
Откройте вкладки chatgpt.com и chat.deepseek.com в этом Chrome.

🏃 Запуск
bash
python run_agent.py
Или для теста самокоррекции:

bash
python test_self_correction.py
📂 Структура проекта
agent/browser_manager.py — единое подключение к CDP.

agent/providers/ — адаптеры для ChatGPT и DeepSeek.

agent/loop.py — главный цикл агента (мозг).

agent/tools.py — инструменты (файлы, команды).

agent/memory.py — сохранение контекста между задачами.
