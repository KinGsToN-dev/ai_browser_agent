import os
import subprocess
import re
from pathlib import Path
from agent.safety import is_command_safe

SANDBOX_DIR = Path("C:/projects/ai_browser_agent/workspace").resolve()

def _safe_path(path_str: str) -> Path:
    target = (SANDBOX_DIR / path_str).resolve()
    if not target.is_relative_to(SANDBOX_DIR):
        raise ValueError(f"Доступ запрещен")
    return target

def _fix_python_indentation(code: str) -> str:
    """Простая починка: если строка заканчивается на ':', следующая строка получает +4 пробела."""
    lines = code.split("\n")
    result = []
    indent = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append("")
            continue
        
        # Если строка содержит def, if, for, while, try, except, else, elif
        if re.match(r'^(def |if |elif |else:|for |while |try:|except |finally:)', stripped):
            # Сбрасываем отступ для нового блока
            indent = 0
            result.append(" " * indent + stripped)
            indent = 4  # Следующая строка должна быть с отступом
        elif stripped.startswith("return ") or stripped.startswith("raise ") or stripped.startswith("pass"):
            result.append(" " * indent + stripped)
        else:
            result.append(" " * indent + stripped)
    return "\n".join(result)

def write_file(path: str, content: str) -> dict:
    try:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        
        # Убираем возможные Markdown-обертки
        if content.startswith("```python"):
            content = content.replace("```python", "").replace("```", "").strip()
            
        if path.endswith(".py"):
            content = _fix_python_indentation(content)
            
        p.write_text(content, encoding="utf-8")
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def read_file(path: str) -> dict:
    try:
        p = _safe_path(path)
        if not p.exists(): return {"ok": False, "error": "Нет файла"}
        return {"ok": True, "content": p.read_text(encoding="utf-8")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def list_dir(path: str = ".") -> dict:
    try:
        p = _safe_path(path)
        if not p.exists(): return {"ok": False, "error": "Нет папки"}
        items = [f"[{'dir' if i.is_dir() else 'file'}] {i.name}" for i in p.iterdir()]
        return {"ok": True, "items": sorted(items)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def run(cmd: str, timeout: int = 60) -> dict:
    is_safe, reason = is_command_safe(cmd)
    if not is_safe: return {"ok": False, "error": f"Блок: {reason}"}
    try:
        res = subprocess.run(cmd, shell=True, cwd=str(SANDBOX_DIR), capture_output=True, text=True, timeout=timeout)
        return {"ok": res.returncode == 0, "stdout": res.stdout, "stderr": res.stderr, "exit_code": res.returncode}
    except Exception as e:
        return {"ok": False, "error": str(e)}
