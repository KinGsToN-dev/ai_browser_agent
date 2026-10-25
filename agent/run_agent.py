# run_agent.py
import logging
from agent.loop import AgentLoop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    agent = AgentLoop()
    
    # Задача для проверки: попросим написать простой код и протестировать его
    task = """
    Напиши на Python функцию is_even(n), которая возвращает True, если число четное.
    Создай файл math_utils.py с этой функцией.
    Создай файл test_math_utils.py с тестами для неё (используй pytest).
    Запусти pytest, убедись что тесты проходят. Если нет — исправь.
    Когда всё будет готово, вызови done.
    """
    
    result = agent.execute(task, max_steps=15)
    print("\n=== РЕЗУЛЬТАТ ===")
    print(result)