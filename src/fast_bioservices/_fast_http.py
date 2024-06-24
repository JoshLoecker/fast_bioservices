import hashlib
import json
import lzma
import pickle
import urllib
import urllib.error
import urllib.parse
import urllib.request
import urllib.response
from abc import ABC
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from http.client import HTTPResponse
from pathlib import Path
from typing import List, Literal, Optional, Type, TypeVar, Union, overload

from rich.progress import BarColumn, Progress, TimeRemainingColumn

from fast_bioservices._log import logger
from fast_bioservices._settings import cache_dir

Method = Literal["GET"]
ResponseType = TypeVar("ResponseType", bound="Response")

class Response:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_from_class_method"):
            raise NotImplementedError("Use `from_response` or `from_cache` to create a Response object")
        return super().__new__(cls)

    def __init__(self) -> None:
        self._url: str
        self._headers: dict
        self._debug_level: int
        self._content: bytes
        self._status: int
        self._method: Method

    @property
    def url(self) -> str:
        return self._url

    @property
    def headers(self) -> dict:
        return self._headers

    @property
    def bytes(self) -> bytes:
        return self._content

    @property
    def text(self) -> str:
        return self.bytes.decode()

    @property
    def json(self) -> dict:
        return json.loads(self.text)

    def cache_object(self) -> dict:
        return {
            "url": self._url,
            "headers": self._headers,
            "debug_level": self._debug_level,
            "content": self._content,
            "status": self._status,
            "method": self._method,
        }

    @overload
    @classmethod
    def create(cls: Type[ResponseType], response: HTTPResponse, method: Method) -> "Response": ...

    @overload
    @classmethod
    def create(cls: Type[ResponseType], *, data: dict) -> "Response": ...  # Use `*` to force keyword-only arguments

    @classmethod
    def create(cls: Type[ResponseType], response=None, method=None, data=None) -> "Response":
        if response is not None and method is not None:
            return cls._from_response(response, method)
        elif data is not None:
            return cls._from_cache(data)
        else:
            raise ValueError("Either (`response` and `method`) or (`data`) must be provided")

    @classmethod
    def _from_response(cls, response: HTTPResponse, method: Method) -> "Response":
        # Ensure that the classmethod is called from `create`
        cls._from_class_method = True
        instance = cls()
        delattr(cls, "_from_class_method")

        instance._url = response.geturl()
        instance._headers = dict(response.getheaders())
        instance._debug_level = response.debuglevel
        instance._content = response.read()
        instance._status = response.getcode()
        instance._method = method
        return instance

    @classmethod
    def _from_cache(cls, data: dict) -> "Response":
        # Ensure that the classmethod is called from `create`
        cls._from_class_method = True
        instance = cls()
        delattr(cls, "_from_class_method")

        instance._url = data["url"]
        instance._headers = data["headers"]
        instance._debug_level = data["debug_level"]
        instance._content = data["content"]
        instance._method = data["method"]
        return instance

class FastHTTP(ABC):
    def __init__(
        self,
        cache: bool,
        workers: int,
        show_progress: bool,
        max_requests_per_second: Optional[int],
    ) -> None:
        self._max_requests_per_second: int = int(1e10) if max_requests_per_second is None else max_requests_per_second
        self._maximum_allowed_workers: int = 16
        self._use_cache: bool = cache
        self._show_progress: bool = show_progress
        self._workers: int = self._set_workers(workers)

        self._cache_dirpath: Path = cache_dir
        self._requests_made: int = 0
        self._last_request_time: float = 0

        self._thread_pool = ThreadPoolExecutor(max_workers=self._workers)
        self._progress = Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "{task.completed}/{task.total} batches",
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
        )

    def _set_workers(self, value: int) -> int:
        if value < 1:
            logger.debug("`max_workers` must be greater than 0, setting to 1")
            value = 1
        elif value > self._maximum_allowed_workers:
            logger.debug(
                f"`max_workers` must be less than {self._maximum_allowed_workers} (received {value}), setting to {self._maximum_allowed_workers}"
            )
            value = self._maximum_allowed_workers
        return value

    @property
    def workers(self) -> int:
        return self._workers

    @workers.setter
    def workers(self, value: int) -> None:
        self._workers = self._set_workers(value)

    def __del__(self):
        self._thread_pool.shutdown(wait=True)

    @property
    def show_progress(self) -> bool:
        return self._show_progress

    @show_progress.setter
    def show_progress(self, value: bool) -> None:
        self._show_progress = value

    def _make_safe_url(self, urls: Union[str, List[str]]) -> List[str]:
        # Safe characters from https://stackoverflow.com/questions/695438
        safe = "&$+,/:;=?@#"
        if isinstance(urls, str):
            return [urllib.parse.quote(urls, safe=safe)]
        return [urllib.parse.quote(url, safe=safe) for url in urls]

    def _calculate_cache_key(self, url: str) -> Path:
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = Path(self._cache_dirpath, cache_key)
        return cache_file

    def __get_without_cache(self, url: str, headers: dict) -> Response:
        request = urllib.request.Request(url, headers=headers)
        response: HTTPResponse = urllib.request.urlopen(request)
        return Response.create(response=response, method="GET")

    def __get_from_cache(self, url: str, headers: dict) -> Optional[Response]:
        cache_file = self._calculate_cache_key(url)
        if cache_file.exists():
            logger.debug(f"Cache hit: {url}")
            with lzma.open(cache_file, "rb") as cache_file:
                return Response.create(data=pickle.load(cache_file))
        return None

    def _save_to_cache(self, response: Response) -> None:
        cache_filepath = self._calculate_cache_key(response.url)
        with lzma.open(cache_filepath, "wb") as cache_file:
            pickle.dump(response.cache_object(), cache_file)

    def _get(
        self,
        urls: Union[str, List[str]],
        headers: Optional[dict] = None,
        temp_disable_cache: bool = False,
    ) -> List[Response]:
        headers = headers or {}
        urls = self._make_safe_url(urls)
        task = self._progress.add_task("[cyan]Working...", total=len(urls)) if self._progress else None
        callable = self.__get_from_cache if self._use_cache and not temp_disable_cache else self.__get_without_cache

        responses: List[Response] = []
        futures: List[Future[Union[Response, None]]] = [
            self._thread_pool.submit(callable, url, headers) for (url, headers) in zip(urls, [headers] * len(urls))
        ]

        for url, future in zip(urls, as_completed(futures)):
            response = future.result()
            if response is not None:
                responses.append(response)
            else:
                responses.append(self.__get_without_cache(url, headers))
                if self._use_cache:
                    self._save_to_cache(responses[-1])
            if self._progress and task is not None:
                self._progress.update(task, advance=1)

        return responses


if __name__ == "__main__":
    http = FastHTTP(cache=True, workers=2, show_progress=True, max_requests_per_second=10)
