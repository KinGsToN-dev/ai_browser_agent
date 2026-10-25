# run_task2.py
import logging
from agent.loop import AgentLoop
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    agent = AgentLoop()
    # Задача, которая требует понимания, что файл math_utils.py уже существует
    task = """
    В проекте уже есть файл math_utils.py.
    Добавь в него функцию is_odd(n), которая возвращает True для нечетных чисел.
    Добавь тесты для is_odd в файл test_math_utils.py.
    Запусти pytest, убедись что все тесты (старые и новые) проходят.
    """
    
    result = agent.execute(task, max_steps=15)
    print("\n=== РЕЗУЛЬТАТ ===")
    print(result)