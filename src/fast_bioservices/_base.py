from abc import ABC


class BaseModel(ABC):
    def __init__(self, url: str):
        self._url: str = url

    @property
    def url(self) -> str:
        return self._url
