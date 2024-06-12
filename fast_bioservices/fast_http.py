import hashlib
import json
import pickle
import time
import urllib
import urllib.error
import urllib.parse
import urllib.request
import urllib.response
from abc import ABC
from http.client import HTTPResponse
from pathlib import Path
from typing import Literal, Optional, Type, TypeVar, overload

from fast_bioservices.log import logger
from fast_bioservices.settings import cache_dir

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
        self._method: Method

    @property
    def bytes(self) -> bytes:
        return self._content

    @property
    def text(self) -> str:
        return self.bytes.decode()

    @property
    def json(self) -> dict:
        return json.loads(self.text)

    def to_cache(self) -> dict:
        return {
            "url": self._url,
            "headers": self._headers,
            "debug_level": self._debug_level,
            "content": self._content,
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
            raise ValueError("Either `response` and `method` or `data` must be provided")

    @classmethod
    def _from_response(cls, response: HTTPResponse, method: Method) -> "Response":
        # Ensure that the classmethod is called from `create`
        cls._from_class_method = True
        instance = cls()
        delattr(cls, "_from_class_method")

        instance._url = response.url
        instance._headers = dict(response.getheaders())
        instance._debug_level = response.debuglevel
        instance._content = response.read()
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
    _cache: Optional[bool] = None

    def __init__(
        self,
        cache: bool,
        max_requests_per_second: Optional[int] = None,
    ) -> None:
        self._use_cache: bool = cache
        self._cache_dirpath: Path = cache_dir

        self._requests_made: int = 0
        self._last_request_time: float = 0
        self._max_requests_per_second: int = int(1e10)
        if max_requests_per_second is not None:
            self._max_requests_per_second = max_requests_per_second

    def _get_without_cache(self, url: str) -> Response:
        return Response.create(urllib.request.urlopen(url), method="GET")

    def _get_from_cache(self, url: str, cache_file: Path) -> Optional[Response]:
        if cache_file.exists():
            logger.debug(f"Cache hit: {url}")
            return Response.create(data=pickle.load(cache_file.open("rb")))
        return None

    def _save_to_cache(self, response: Response, cache_file: Path) -> None:
        pickle.dump(response.to_cache(), cache_file.open("wb"))

    def _get(
        self,
        url: str,
        temp_disable_cache: bool = False,
    ) -> Response:
        url = urllib.parse.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
        parts = urllib.parse.urlparse(url)

        logger.debug(f"Getting {url}")

        # Perform rate limiting
        time_since_last_request = time.time() - self._last_request_time
        if time_since_last_request < 1 / self._max_requests_per_second:
            time.sleep(1 / self._max_requests_per_second - time_since_last_request)
        self._last_request_time = time.time()

        cache_key = hashlib.blake2b(url.encode()).hexdigest()
        cache_file = Path(self._cache_dirpath, cache_key)
        try:
            if self._use_cache and not temp_disable_cache:
                response = self._get_from_cache(url, cache_file)
                if response is None:
                    response = self._get_without_cache(url)
                    self._save_to_cache(response, cache_file)
            else:
                response = self._get_without_cache(url)
        except urllib.error.URLError as e:
            logger.error(f"Could not connect to {parts.netloc + parts.path}")
            raise e

        return response


if __name__ == "__main__":
    http = FastHTTP(cache=True)
