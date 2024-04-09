import time
import urllib
import urllib.parse
import urllib.request
from abc import ABC
from typing import Any, List, Mapping, Optional, Sequence, Union

import httpx
import httpx_cache

from fast_bioservices.log import logger
from fast_bioservices.settings import cache_name


class FastHTTP(ABC):
    _cache: Optional[bool] = None
    _client: httpx_cache.Client = httpx_cache.Client(
        cache=httpx_cache.FileCache(cache_name),
        timeout=30,
    )

    def __init__(
        self,
        cache: bool,
        max_requests_per_second: Optional[int] = None,
    ) -> None:
        self._use_cache: bool = cache
        self._max_requests_per_second: int = int(1e10)
        if max_requests_per_second is not None:
            self._max_requests_per_second = max_requests_per_second

        if not self._use_cache:
            FastHTTP._client.headers["cache-control"] = "no-cache"
        self._client = FastHTTP._client

        self._requests_made: int = 0
        self._last_request_time: float = 0

    def __del__(self):
        self._client.close()

    def _get(
        self,
        url: str,
        temp_disable_cache: bool = False,
    ) -> httpx.Response:
        parts = urllib.parse.urlparse(url)
        url = urllib.parse.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
        logger.debug(f"Getting {url}")

        # Perform rate limiting
        time_since_last_request = time.time() - self._last_request_time
        if time_since_last_request < 1 / self._max_requests_per_second:
            time.sleep(1 / self._max_requests_per_second - time_since_last_request)
        self._last_request_time = time.time()

        try:
            if temp_disable_cache:
                self._client.headers["cache-control"] = "no-cache"
                response = self._client.get(url)
                self._client.headers.pop("cache-control")
            else:
                response = self._client.get(url)
        except httpx.ConnectError as e:
            logger.error(f"Could not connect to {parts.netloc + parts.path}")
            raise e
        return response


if __name__ == "__main__":
    http = FastHTTP(cache=True)
