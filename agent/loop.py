# agent/loop.py
import json
import logging
import re
from agent.browser import BrowserAgent
from agent import tools
from agent import memory

log = logging.getLogger("loop")

SYSTEM_PROMPT = """Ты — автономный ИИ-агент, работающий в строгом цикле. 
Ты НЕ МОЖЕШЬ выполнять действия напрямую. Ты можешь только ВЫЗЫВАТЬ ИНСТРУМЕНТЫ.
Твои слова не имеют силы, пока ты не вызовешь инструмент.

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
1. read_file(path: str)
2. write_file(path: str, content: str)
3. list_dir(path: str)
4. run(cmd: str)
5. done(summary: str)

ПРАВИЛА:
1. Ты должен отвечать ТОЛЬКО валидным JSON-объектом, без markdown и лишнего текста.
2. Формат ответа: {"tool": "имя_инструмента", "args": {"arg1": "val1"}}
3. НЕ ВРИ, что ты что-то сделал. Если нужно создать файл — вызывай write_file. Если нужно запустить тесты — вызывай run.
4. Вызвать done можно ТОЛЬКО после того, как ты реально выполнил нужные действия через инструменты.
"""

class AgentLoop:
    def __init__(self):
        self.agent = BrowserAgent()
        self.history = []

    def _parse_json(self, text: str) -> dict:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                text = text[start:end+1]
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Не удалось распарсить JSON: {e}\nТекст ответа: {text}")

    def execute(self, task: str, max_steps: int = 15) -> str:
        log.info(f"=== НАЧАЛО ЗАДАЧИ: {task.strip()} ===")
        
        # 1. Читаем память о прошлых задачах
        past_context = memory.load_context()
        context_block = f"КОНТЕКСТ ПРЕДЫДУЩИХ ЗАДАЧ:\n{past_context}\n" if past_context else ""

        prompt = f"{SYSTEM_PROMPT}\n\n{context_block}\nЗАДАЧА: {task}\n\nВызови первый инструмент."
        self.history = [prompt]

        files_written = 0
        commands_run = 0

        for step in range(1, max_steps + 1):
            log.info(f"--- Шаг {step} ---")
            
            try:
                response_text = self.agent.ask("\n".join(self.history))
                action = self._parse_json(response_text)
                tool_name = action.get("tool")
                args = action.get("args", {})
            except Exception as e:
                log.error(f"Ошибка парсинга/запроса: {e}")
                self.history.append(f"Ошибка: {e}. Ответь ТОЛЬКО валидным JSON.")
                continue

            log.info(f"Агент выбрал: {tool_name} {args}")

            # Защита от вранья
            if tool_name == "done":
                if files_written == 0 and ("напиши" in task.lower() or "создай" in task.lower()):
                    log.warning("Агент пытается вызвать done, но не создал ни одного файла! Отклоняем.")
                    self.history.append("Ошибка: ты пытаешься завершить задачу, но не создал ни одного файла через write_file.")
                    continue
                if commands_run == 0 and "тест" in task.lower():
                    log.warning("Агент пытается вызвать done, но не запустил ни одной команды! Отклоняем.")
                    self.history.append("Ошибка: ты пытаешься завершить задачу, но не запустил тесты через run.")
                    continue
                
                summary = args.get("summary", "Задача выполнена.")
                log.info(f"=== ЗАДАЧА ЗАВЕРШЕНА: {summary} ===")
                memory.save_context(summary) # 2. Сохраняем финальный результат в память
                self.agent.close()
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

                # 3. Записываем шаг в файл steps.jsonl
                memory.log_step(step, tool_name, args, result)

                result_str = json.dumps(result, ensure_ascii=False)
                log.info(f"Результат: {result_str[:150]}...")
                self.history.append(f"Вызов: {json.dumps(action, ensure_ascii=False)}")
                self.history.append(f"Результат: {result_str}")
                self.history.append("Что делаем дальше?")
            else:
                log.warning(f"Неизвестный инструмент: {tool_name}")
                self.history.append(f"Ошибка: инструмента '{tool_name}' не существует.")

        log.warning(f"=== ЛИМИТ ШАГОВ ({max_steps}) ===")
        self.agent.close()
        return "Задача не была завершена."