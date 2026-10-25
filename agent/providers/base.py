from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def send(self, text: str):
        pass

    @abstractmethod
    def wait_answer(self, timeout_sec=240, stable_sec=2.0) -> str:
        pass

    @abstractmethod
    def check_limit(self) -> bool:
        """Проверяет, не уперлись ли мы в лимит сообщений"""
        pass

    @abstractmethod
    def start_new_chat(self):
        """Создает новый чат (нажимает кнопку New Chat)"""
        pass

    @abstractmethod
    def close(self):
        pass
