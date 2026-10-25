# agent/memory.py
import json
from pathlib import Path
import time

STEPS_FILE = Path("steps.jsonl")
CONTEXT_FILE = Path("CONTEXT.md")

def log_step(step_num: int, tool: str, args: dict, result: dict):
    """Записывает один шаг агента в лог."""
    record = {
        "timestamp": time.time(),
        "step": step_num,
        "tool": tool,
        "args": args,
        "result": result
    }
    # Открываем файл в режиме 'a' (append) и пишем одну строку JSON
    with STEPS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def load_context() -> str:
    """Читает сводку из предыдущих сессий (если есть)."""
    if CONTEXT_FILE.exists():
        return CONTEXT_FILE.read_text(encoding="utf-8")
    return ""

def save_context(summary: str):
    """Сохраняет финальную сводку задачи, чтобы агент помнил её в будущем."""
    with CONTEXT_FILE.open("w", encoding="utf-8") as f:
        f.write(f"# Последняя выполненная задача\n\n{summary}\n")