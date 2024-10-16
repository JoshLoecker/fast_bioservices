from __future__ import annotations

import hashlib
import lzma
import pickle
import time
import urllib
import urllib.error
import urllib.parse
import urllib.request
import urllib.response
from abc import ABC
from concurrent.futures import Future, ThreadPoolExecutor, wait
from http.client import HTTPResponse
from pathlib import Path
from typing import List, Literal

from loguru import logger

from fast_bioservices.settings import cache_dir

Method = Literal["GET"]


class FastHTTP(ABC):
    def __init__(
        self,
        *,
        cache: bool,
        workers: int,
        max_requests_per_second: int | None,
    ) -> None:
        self._max_requests_per_second: int = float("inf") if max_requests_per_second is None else max_requests_per_second
        self._maximum_allowed_workers: int = 5
        self._use_cache: bool = cache
        self._workers: int = self._set_workers(workers)

        self._cache_dirpath: Path = cache_dir
        self._non_cached_requests_made: int = 0
        self._last_request_time: float = 0

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

    def _calculate_cache_key(self, url: str) -> Path:
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = Path(self._cache_dirpath, cache_key)
        return cache_file

    def __get_without_cache(self, url: str, headers: dict, log_on_complete: bool) -> bytes:
        # Rate limiting
        self._non_cached_requests_made += 1
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        if self._non_cached_requests_made > self._max_requests_per_second and time_since_last_request < 1:
            time.sleep(1 - time_since_last_request)
            self._non_cached_requests_made -= self._max_requests_per_second
        self._last_request_time = current_time

        request = urllib.request.Request(url, headers=headers)
        try:
            response: HTTPResponse = urllib.request.urlopen(request)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return b""
            raise e

        content: bytes = response.read()
        if self._use_cache:
            self._save_to_cache(url, content=content)
        if log_on_complete:
            self._log_on_complete_callback("without cache")

        return content

    def __get_from_cache(self, url: str, headers: dict, log_on_complete: bool) -> bytes | None:
        cache_file = self._calculate_cache_key(url)
        if cache_file.exists():
            with lzma.open(cache_file) as cache_file:
                if log_on_complete:
                    self._log_on_complete_callback("with cache")  # Only log when the cache file is found
                return pickle.load(cache_file)
        return None

    def _save_to_cache(self, url: str, content: bytes) -> None:
        cache_filepath = self._calculate_cache_key(url)
        with lzma.open(cache_filepath, "wb") as cache_file:
            pickle.dump(obj=content, file=cache_file)

    def _get(
        self,
        urls: str | List[str],
        headers: dict | None = None,
        temp_disable_cache: bool = False,
        log_on_complete: bool = True,
    ) -> List[bytes]:
        headers = headers or {}
        urls = self._make_safe_url(urls)

        self._current_requests = 0
        self._total_requests = len(urls)

        callable_ = self.__get_from_cache if (self._use_cache and not temp_disable_cache) else self.__get_without_cache

        futures: list[Future[bytes]] = []
        url_mapping: dict[Future, str] = {}
        for url in urls:
            future = self._thread_pool.submit(callable_, url=url, headers=headers, log_on_complete=log_on_complete)
            futures.append(future)
            url_mapping[future] = url

        responses: List[bytes] = []
        while futures:
            for future in wait(futures).done:
                try:
                    result = future.result()
                    url = url_mapping[future]
                    if result is None:  # Cache miss
                        new_future = self._thread_pool.submit(self.__get_without_cache, url=url, headers=headers, log_on_complete=log_on_complete)
                        futures.append(new_future)
                        url_mapping[new_future] = url
                    else:  # Cache hit
                        responses.append(result)
                except Exception as e:
                    logger.error(f"Error in future: {e}")
                    raise e
                finally:
                    futures.remove(future)

        return responses


if __name__ == "__main__":
    http = FastHTTP(cache=True, workers=2, max_requests_per_second=10)
