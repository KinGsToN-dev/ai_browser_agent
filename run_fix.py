import logging
from agent.loop import AgentLoop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    agent = AgentLoop()
    
    task = """
    В папке workspace есть файл broken.py с функцией add(a, b).
    Она должна возвращать сумму, но возвращает разность.
    
    1. Создай файл test_broken.py с тестами:
       - Проверь, что add(2, 3) == 5.
       - Проверь, что add(-1, 1) == 0.
    2. Запусти pytest.
    3. Ты увидишь, что тесты падают (FAILED).
    4. Прочитай broken.py, найди ошибку и исправь её.
    5. Снова запусти pytest. Убедись, что тесты проходят.
    6. Вызови done.
    """
    
    result = agent.execute(task, max_steps=15)
    print("\n=== РЕЗУЛЬТАТ ===")
    print(result)