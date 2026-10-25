import logging
from agent.loop import AgentLoop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    agent = AgentLoop()
    
    task = """
    Напиши функцию divide(a, b) в файле calculator.py.
    Если b равно 0, функция должна ВОЗВРАЩАТЬ 0 (а не выбрасывать ошибку).
    Затем напиши тесты в test_calculator.py, которые проверяют:
    1. Обычное деление (10 / 2 = 5).
    2. Деление на ноль (10 / 0 = 0).
    Запусти pytest. Если тесты не проходят — исправь код.
    Когда всё будет готово, вызови done.
    """
    
    result = agent.execute(task, max_steps=15)
    print("\n=== РЕЗУЛЬТАТ ===")
    print(result)
