from abc import ABC

from fast_bioservices.log import logger


class BaseModel(ABC):
    def __init__(self, url: str):
        self._url: str = url

    @property
    def url(self) -> str:
        return self._url

    @property
    def max_workers(self) -> int:
        return self._max_workers

    @max_workers.setter
    def max_workers(self, value: int) -> None:
        if value < 1:
            logger.debug("`max_workers` must be greater than 0, setting to 1")
            value = 1
        elif value > self._max_workers:
            logger.debug(f"`max_workers` must be less than 10 (received {value}), setting to 10")
            value = 10

        self._max_workers = value
