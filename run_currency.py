import logging
from agent.loop import AgentLoop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    agent = AgentLoop()
    
    task = """
    1. Создай файл currency.py.
    2. Напиши функцию convert_to_usd(amount, rate), которая переводит сумму в доллары по курсу.
       - Если amount отрицательный, возвращать 0.
       - Если rate меньше или равен 0, возвращать 0.
       - Иначе возвращать amount * rate.
    3. Создай файл test_currency.py с тестами (pytest):
       - Проверь обычный перевод (100 * 0.9 = 90).
       - Проверь отрицательную сумму (-50 * 0.9 = 0).
       - Проверь нулевой курс (100 * 0 = 0).
    4. Запусти pytest. Если тесты падают — исправь код.
    5. Вызови done.
    """
    
    result = agent.execute(task, max_steps=20)
    print("\n=== РЕЗУЛЬТАТ ===")
    print(result)