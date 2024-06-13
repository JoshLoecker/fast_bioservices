from abc import ABC, abstractmethod


class BaseModel(ABC):
    def __init__(self, show_progress: bool = True):
        self._max_workers: int = 10
        self._show_progress: bool = show_progress

    @property
    @abstractmethod
    def url(self) -> str: ...
