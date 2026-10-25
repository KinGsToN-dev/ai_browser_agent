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

    def _parse_json(self, text: str) -> dict:
        # 1. Ищем ```json ... ```
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match: text = match.group(1)
        else:
            # 2. Ищем просто {...}
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                text = text[start:end+1]
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 3. Пытаемся экранировать все кавычки и распарсить
            log.warning("Пытаюсь экранировать JSON...")
            try:
                # Находим content и экранируем внутренние кавычки
                fixed = re.sub(r'(?<!\\)"', '\\"', text)
                fixed = fixed.replace('\\"tool\\"', '"tool"').replace('\\"args\\"', '"args"')
                return json.loads(fixed)
            except Exception as e:
                raise ValueError(f"Не удалось распарсить JSON: {e}\nТекст: {text}")

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

        prompt = f"{SYSTEM_PROMPT}\n\n{context_block}\nЗАДАЧА: {task}\n\nВызови первый инструмент."
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
                self.provider.send("\n".join(self.history))
                response_text = self.provider.wait_answer()
                action = self._parse_json(response_text)
                tool_name = action.get("tool")
                args = action.get("args", {})
            except Exception as e:
                log.error(f"Ошибка: {e}")
                self.history.append(f"Ошибка: {e}. Ответь ТОЛЬКО JSON без Markdown.")
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
                if files_written == 0:
                    self.history.append("Ты не создал файлов!")
                    continue
                if commands_run == 0:
                    self.history.append("Ты не запустил тесты!")
                    continue
                
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
