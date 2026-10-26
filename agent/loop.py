import json
import logging
import re
from agent import tools
from agent import memory
from agent.providers.chatgpt import ChatGPTProvider
from agent.providers.deepseek import DeepSeekProvider
from agent.browser_manager import BrowserManager

log = logging.getLogger("loop")

SYSTEM_PROMPT = """Ты — автономный ИИ-агент. Ты управляешь файлами и командами через инструменты.

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
1. read_file(path: str)
2. write_file(path: str, content: str)
3. list_dir(path: str)
4. run(cmd: str)
5. done(summary: str)

ВАЖНО:
- НЕ используй Markdown-обертки (```) внутри JSON. Просто пиши код как строку с \n (перенос строки) и пробелами.
- Пример правильного ответа: {"tool": "write_file", "args": {"path": "calc.py", "content": "def foo():\n    return 1\n"}}
- НЕ ИСПОЛЬЗУЙ python -c "...". Только "pytest" или "python file.py".
- Вызвать done можно ТОЛЬКО когда тесты прошли (exit_code=0).
"""

class AgentLoop:
    def __init__(self, provider=None):
        self.provider = provider if provider else ChatGPTProvider()
        self.fallback_provider = None
        self.history = []
        self.last_action = None

    def _parse_markdown(self, text: str) -> dict:
        # 1. Ищем блок с кодом (```python ... ```)
        code_match = re.search(r'```(?:python)?\s*(.*?)\s*```', text, re.DOTALL)
        if code_match:
            code = code_match.group(1)
            # Ищем имя файла перед блоком (например, "Создаю файл calc.py")
            file_match = re.search(r'Создаю файл\s+([\w\.]+)', text)
            if not file_match:
                file_match = re.search(r'файл\s+([\w\.]+)', text)
            filename = file_match.group(1) if file_match else "main.py"
            return {"tool": "write_file", "args": {"path": filename, "content": code}}

        # 2. Ищем команду для запуска
        cmd_match = re.search(r'Запускаю команду\s+(.+)', text)
        if cmd_match:
            return {"tool": "run", "args": {"cmd": cmd_match.group(1).strip()}}

        # 3. Ищем завершение
        if "Задача выполнена" in text:
            return {"tool": "done", "args": {"summary": text.strip()}}

        return {"tool": "error", "args": {"message": "Не понял команду. Напиши 'Создаю файл ...' или 'Запускаю команду ...'"}}
            
    def _switch_provider(self):
        if isinstance(self.provider, DeepSeekProvider):
            return False
        log.warning("Переключаюсь на DeepSeek...")
        try:
            self.fallback_provider = DeepSeekProvider()
            self.provider = self.fallback_provider
            return True
        except Exception as e:
            log.error(f"Ошибка переключения: {e}")
            return False

    def execute(self, task: str, max_steps: int = 15) -> str:
        log.info(f"=== НАЧАЛО ЗАДАЧИ: {task.strip()} ===")
        
        past_context = memory.load_context()
        context_block = f"КОНТЕКСТ:\n{past_context}\n" if past_context else ""
        
        prompt = f"""Ты — автономный ИИ-агент. Ты управляешь файлами и командами.

        ФОРМАТ ОТВЕТА:
        1.Если нужно создать файл, напиши:
        Создаю файл <имя_файла>
        <КОД_ЗДЕСЬ>
        2.Если нужно запустить тесты, напиши:
        Запускаю команду <команда>
        3.Если задача выполнена, напиши:
        Задача выполнена. <итог>

        ПРАВИЛА:
        1.Пиши код в формате ```python (начни с трех обратных кавычек и слова python, закончи тремя обратными кавычками).
        2.Используй только имена файлов (без путей).
        3.Не пиши лишнего текста, только команды.
        4.Сначала создай файлы, потом запускай тесты.

        {context_block}
        ЗАДАЧА: {task}
        """
        self.history = [prompt]

        files_written = 0
        commands_run = 0

        for step in range(1, max_steps + 1):
            log.info(f"--- Шаг {step} ---")
            
            if self.provider.check_limit():
                log.warning("Лимит!")
                if not self._switch_provider(): break
                self.provider.start_new_chat()
                self.provider.send(f"Продолжаем (шаг {step}).")

            try:
                if step == 1:
                    self.provider.send(prompt)
                else:
                    self.provider.send("\n".join(self.history))
                
                response_text = self.provider.wait_answer()
                action = self._parse_markdown(response_text)
                tool_name = action.get("tool")
                args = action.get("args", {})
            except Exception as e:
                log.error(f"Ошибка: {e}")
                self.history.append(f"Ошибка: {e}.")
                continue

            current_action_str = json.dumps(action, sort_keys=True)
            if self.last_action == current_action_str:
                log.warning("Повтор!")
                self.history.append("Ошибка: ты повторяешь действие. Сделай что-то другое.")
                self.last_action = None
                continue
            self.last_action = current_action_str

            log.info(f"Агент выбрал: {tool_name} {args}")

            if tool_name == "done":
                summary = args.get("summary", "Готово.")
                log.info(f"=== ЗАВЕРШЕНО: {summary} ===")
                memory.save_context(summary)
                BrowserManager().close()
                return summary

            elif hasattr(tools, tool_name):
                func = getattr(tools, tool_name)
                try:
                    result = func(**args)
                except Exception as e:
                    result = {"ok": False, "error": str(e)}
                
                if result.get("ok"):
                    if tool_name == "write_file": files_written += 1
                    if tool_name == "run": commands_run += 1

                memory.log_step(step, tool_name, args, result)
                result_str = json.dumps(result, ensure_ascii=False)
                log.info(f"Результат: {result_str[:150]}...")
                
                if tool_name == "run" and not result.get("ok"):
                    self.history.append(f"Результат (ОШИБКА): {result_str}")
                    self.history.append("Тесты упали! Исправь код.")
                else:
                    self.history.append(f"Результат: {result_str}")
                    self.history.append("Что дальше?")
            else:
                self.history.append(f"Нет инструмента '{tool_name}'.")

        log.warning("=== ЛИМИТ ШАГОВ ===")
        BrowserManager().close()
        return "Задача не завершена."
    
      
