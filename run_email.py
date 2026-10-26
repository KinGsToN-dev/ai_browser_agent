import logging
from agent.loop import AgentLoop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    agent = AgentLoop()
    
    task = """
    1. Создай файл email_validator.py.
    2. Напиши функцию is_valid_email(email), которая проверяет, является ли строка валидным email.
       - Должна содержать символ '@' и точку после него (например, user@example.com).
       - Не должна содержать пробелов.
       - Возвращает True или False.
    3. Создай файл test_email_validator.py с тестами (pytest):
       - Проверь валидный email ('test@example.com').
       - Проверь email без '@' ('testexample.com').
       - Проверь email с пробелом ('test @example.com').
       - Проверь email без точки после '@' ('test@example').
    4. Запусти pytest. Если тесты падают — исправь код.
    5. Вызови done.
    """
    
    result = agent.execute(task, max_steps=20)
    print("\n=== РЕЗУЛЬТАТ ===")
    print(result)