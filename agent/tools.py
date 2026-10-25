# agent/tools.py
import os
import subprocess
from pathlib import Path
from agent.safety import is_command_safe

# Корень песочницы (все файловые операции ограничены этой папкой)
SANDBOX_DIR = Path("C:/projects/ai_browser_agent/workspace").resolve()

def _safe_path(path_str: str) -> Path:
    """Проверяет, что путь находится внутри песочницы."""
    target = (SANDBOX_DIR / path_str).resolve()
    if not target.is_relative_to(SANDBOX_DIR):
        raise ValueError(f"Доступ запрещен: путь {target} вне песочницы {SANDBOX_DIR}")
    return target

def read_file(path: str) -> dict:
    """Читает текстовый файл из песочницы."""
    try:
        p = _safe_path(path)
        if not p.exists():
            return {"ok": False, "error": f"Файл не найден: {path}"}
        content = p.read_text(encoding="utf-8")
        return {"ok": True, "content": content}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def write_file(path: str, content: str) -> dict:
    """Пишет текст в файл в песочнице (создает папки при необходимости)."""
    try:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def list_dir(path: str = ".") -> dict:
    """Возвращает список файлов и папок."""
    try:
        p = _safe_path(path)
        if not p.exists():
            return {"ok": False, "error": f"Папка не найдена: {path}"}
        
        items = []
        for item in p.iterdir():
            type_str = "dir" if item.is_dir() else "file"
            items.append(f"[{type_str}] {item.name}")
        return {"ok": True, "items": sorted(items)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def run(cmd: str, timeout: int = 60) -> dict:
    """Запускает команду в песочнице с проверкой безопасности."""
    is_safe, reason = is_command_safe(cmd)
    if not is_safe:
        return {"ok": False, "error": f"Заблокировано: {reason}"}

    try:
        # Запускаем команду в папке workspace
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(SANDBOX_DIR),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Timeout ({timeout} сек)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}