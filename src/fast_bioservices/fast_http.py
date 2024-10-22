from __future__ import annotations

import sys
import time
import urllib.parse
from abc import ABC
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

import hishel
import httpcore
import httpx
from hishel._utils import generate_key
from httpx import Request, Response
from loguru import logger

from fast_bioservices.settings import cache_dir

NO_CACHE: str = "no-store, max-age=0"
MAX_CACHE: str = f"max-age={sys.maxsize}"


def _key_generator(request: httpx.Request | httpcore.Request, body: bytes = b"") -> str:
    if isinstance(request, httpx.Request):
        request = httpcore.Request(
            method=str(request.method), url=str(request.url), headers=request.headers, content=request.content, extensions=request.extensions
        )
    key = generate_key(request, body)
    method = request.method.decode("ascii") if isinstance(request.method, bytes) else request.method
    host = request.url.host.decode("ascii") if isinstance(request.url.host, bytes) else request.url.host
    return f"{method}|{host}|{key}"


def _get_cache_path(request: httpx.Request) -> Path:
    return Path(cache_dir, _key_generator(request))


class RateLimit(httpx.BaseTransport):
    """
    Implement rate limiting on httpx transports
    """

    def __init__(self, transport: httpx.BaseTransport, rate: int | float, period: int | float, use_cache: bool):
        self.transport = transport
        self.rate = rate  # Requests per second
        self.period = period  # Time period in seconds
        self.use_cache = use_cache
        self.last_reset = time.time()
        self.requests_in_period = deque(maxlen=rate)
        self._cache_storage: hishel.FileStorage | None = None

    @property
    def cache_storage(self):
        return self._cache_storage

    @cache_storage.setter
    def cache_storage(self, storage):
        self._cache_storage = storage

    def _build_from_cache(self, request: Request) -> Response | None:
        cache_path: Path = _get_cache_path(request)
        if self.use_cache and request.headers["Cache-Control"] != NO_CACHE and cache_path.exists():
            cached_response = self._cache_storage.retrieve(cache_path.stem)
            if isinstance(cached_response, httpcore.Response):
                return httpx.Response(
                    status_code=cached_response.status,
                    headers=cached_response.headers,
                    content=cached_response.content,
                    extensions=cached_response.extensions,
                )
            return self.transport.handle_request(request)
        return None

    def handle_request(self, request: Request) -> Response:
        # Exit early if we are using cache and the key exists
        is_cached = self._build_from_cache(request)
        if is_cached is not None:
            return is_cached

        now = time.time()
        if now - self.last_reset >= self.period:
            self.last_reset = now
            self.requests_in_period.clear()

        while len(self.requests_in_period) >= self.rate:
            time.sleep(1 / self.rate)
            logger.debug(f"Sleeping for {1 / self.rate} seconds")
            now = time.time()
            if now - self.last_reset >= self.period:
                self.last_reset = now
                self.requests_in_period.clear()
                break

        self.requests_in_period.append(now)
        response = self.transport.handle_request(request)
        return response


class FastHTTP(ABC):
    def __init__(
        self,
        *,
        cache: bool,
        workers: int,
        max_requests_per_second: int | None,
    ) -> None:
        self._maximum_allowed_workers: int = 5
        self._use_cache: bool = cache
        self._workers: int = self._set_workers(workers)
        self._transport = RateLimit(transport=httpx.HTTPTransport(), rate=max_requests_per_second, period=1, use_cache=self._use_cache)
        if self._use_cache:
            self._storage = hishel.FileStorage(base_path=cache_dir, ttl=sys.maxsize)
            self._controller = hishel.Controller(key_generator=_key_generator, allow_stale=True, force_cache=True)
            self._client: hishel.CacheClient = hishel.CacheClient(storage=self._storage, controller=self._controller, transport=self._transport)
            self._transport.cache_storage = self._storage
        else:
            self._client: httpx.Client = httpx.Client(transport=self._transport)

        self._current_requests: int = 0
        self._total_requests: int = 0
        self._thread_pool = ThreadPoolExecutor(max_workers=self._workers)

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
        try:
            self._thread_pool.shutdown()
        except AttributeError:
            pass

    @staticmethod
    def _make_safe_url(urls: str | List[str]) -> List[str]:
        # Safe characters from https://stackoverflow.com/questions/695438
        safe = "&$+,/:;=?@#"
        if isinstance(urls, str):
            return [urllib.parse.quote(urls, safe=safe)]
        return [urllib.parse.quote(url, safe=safe) for url in urls]

    def _log_on_complete_callback(self, ending: str):
        self._current_requests += 1
        logger.debug(f"Finished {self._current_requests:>{len(str(self._total_requests))}} of {self._total_requests} ({ending})")

    def _do_get(self, url: str, headers: dict, extensions: dict, log_on_complete: bool) -> bytes:
        try:
            with self._transport:
                response: httpx.Response = self._client.get(url, headers=headers, timeout=60, extensions=extensions)
        except httpx.ReadTimeout as e:
            logger.critical(f"Read timeout error on url: {url}")
            raise e
        except httpx.ConnectTimeout as e:
            logger.critical(f"Connect timeout error on url: {url}")
            raise e
        except httpx.ConnectError as e:
            logger.critical(f"Connect error on url: {url}")
            raise e

        if log_on_complete:
            if "from_cache" in response.extensions.keys():
                if response.extensions["from_cache"]:
                    self._log_on_complete_callback("with cache")
                else:
                    self._log_on_complete_callback("without cache")

        return response.content

    def _get(
        self,
        urls: str | List[str],
        headers: dict | None = None,
        temp_disable_cache: bool = False,
        log_on_complete: bool = True,
        extensions: dict | None = None,
    ) -> List[bytes]:
        urls = self._make_safe_url(urls)
        self._current_requests = 0
        self._total_requests = len(urls)

        headers = headers or {}
        headers["Cache-Control"] = NO_CACHE if temp_disable_cache else MAX_CACHE

        futures: list[Future[bytes]] = []
        url_mapping: dict[Future, str] = {}
        for url in urls:
            future = self._thread_pool.submit(self._do_get, url=url, headers=headers, extensions=extensions, log_on_complete=log_on_complete)
            futures.append(future)
            url_mapping[future] = url

        responses: List[bytes] = [f.result() for f in as_completed(futures)]
        return responses
