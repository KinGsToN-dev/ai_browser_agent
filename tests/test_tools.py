# tests/test_tools.py
import pytest
from agent.tools import read_file, write_file, list_dir, run
from agent.safety import is_command_safe

def test_write_and_read():
    res = write_file("test_dir/hello.txt", "Привет, агент!")
    assert res["ok"] is True
    
    res = read_file("test_dir/hello.txt")
    assert res["ok"] is True
    assert res["content"] == "Привет, агент!"

def test_list_dir():
    write_file("test_dir/hello.txt", "...")
    res = list_dir("test_dir")
    assert res["ok"] is True
    assert "[file] hello.txt" in res["items"]

def test_safe_path_escape():
    # Попытка выйти за пределы песочницы через ../
    res = read_file("../../windows/system32/calc.exe")
    assert res["ok"] is False
    assert "вне песочницы" in res["error"].lower()

def test_command_whitelist():
    # Разрешенное
    assert is_command_safe("pytest")[0] is True
    assert is_command_safe("dir")[0] is True
    
    # Запрещенное
    assert is_command_safe("rm -rf /")[0] is False
    assert is_command_safe("shutdown -s -t 0")[0] is False
    assert is_command_safe("unknown_cmd")[0] is False

def test_run_safe_command():
    res = run("echo Hello")
    assert res["ok"] is True
    assert "Hello" in res["stdout"]

def test_run_forbidden_command():
    res = run("rm -rf /")
    assert res["ok"] is False
    assert "Заблокировано" in res["error"]