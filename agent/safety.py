# agent/safety.py
import shlex

# Список разрешенных команд (первое слово в строке)
ALLOWED_COMMANDS = {
    "pytest", "ruff", "mypy", "python", "git",
    "ls", "dir", "cat", "type", "echo", "mkdir",
}

# Список запрещенных паттернов (на всякий случай, даже если команда в whitelist)
FORBIDDEN_PATTERNS = [
    "rm -rf", "del /f", "format", "shutdown", "reboot",
    "> /dev/sda", "mkfs", "dd if=", "chmod 777", "wget", "curl"
]

def is_command_safe(cmd_str: str) -> tuple[bool, str]:
    """
    Проверяет, безопасно ли выполнять команду.
    Возвращает (True, "") если безопасно, иначе (False, "причина").
    """
    cmd_str = cmd_str.strip()
    if not cmd_str:
        return False, "Пустая команда"

    # Проверка на запрещенные паттерны
    cmd_lower = cmd_str.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in cmd_lower:
            return False, f"Запрещенный паттерн: {pattern}"

    try:
        # Разбиваем строку на токены (учитывая кавычки)
        parts = shlex.split(cmd_str)
        if not parts:
            return False, "Не удалось распарсить команду"

        base_cmd = parts[0].lower()
        
        # Если это вызов python скрипта (python test.py), проверяем только базовую команду
        if base_cmd in ALLOWED_COMMANDS:
            return True, ""
            
        return False, f"Команда '{base_cmd}' не в белом списке"
        
    except Exception as e:
        return False, f"Ошибка парсинга: {e}"