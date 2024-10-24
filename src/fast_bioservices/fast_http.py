from __future__ import annotations

import asyncio
import contextlib
import sys
import time
import urllib.parse
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
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
            method=str(request.method),
            url=str(request.url),
            headers=request.headers,
            content=request.content,
            extensions=request.extensions,
        )
    key = generate_key(request, body)
    method = request.method.decode("ascii") if isinstance(request.method, bytes) else request.method
    host = request.url.host.decode("ascii") if isinstance(request.url.host, bytes) else request.url.host
    return f"{method}|{host}|{key}"


class RateLimitTransport(httpx.AsyncBaseTransport):
    """
    Implement rate limiting on httpx transports; ignores hishel transport cache
    """

    def __init__(self, rate: int | float, use_cache: bool, period: int = 1):
        self._transport = httpx.AsyncHTTPTransport()
        self._rate = rate  # Requests per second
        self._period = period
        self._use_cache = use_cache
        self._last_reset = time.time()
        self._requests_in_period = 0

    async def handle_async_request(self, request: Request) -> Response:
        """
        The rate limiting only takes place if the request is not cached - hishel will not rate limit retrieving cached responses
        :param request:
        :return:
        """
        now = time.time()
        if now - self._last_reset >= self._period:  # We've waited for `period` seconds since last reset, reset counter
            self._last_reset = now
            self._requests_in_period = 0

        while self._requests_in_period >= self._rate:  # We've hit the rate limit, sleep
            logger.trace(f"Sleeping for {1 / self._rate} seconds")
            await asyncio.sleep(1 / self._rate)
            now = time.time()
            if now - self._last_reset >= self._period:  # Make sure that we've waited long enough
                self._last_reset = now
                self._requests_in_period = 0
                break

        self._requests_in_period += 1
        return await self._transport.handle_async_request(request)


class FastHTTP(ABC):
    def __init__(self, *, cache: bool, max_requests_per_second: int | None = 5) -> None:
        self._use_cache: bool = cache
        self._requests_per_second: int = max_requests_per_second
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        transport = RateLimitTransport(rate=max_requests_per_second, use_cache=self._use_cache)
        if self._use_cache:
            self._storage = hishel.AsyncFileStorage(base_path=cache_dir, ttl=sys.maxsize)
            self._controller = hishel.Controller(key_generator=_key_generator, allow_stale=True, force_cache=True)
            self._transport = hishel.AsyncCacheTransport(transport=transport, storage=self._storage, controller=self._controller)
        else:
            self._transport = transport
        self._client: httpx.AsyncClient = httpx.AsyncClient(transport=self._transport, timeout=60)

        self._current_requests: int = 0
        self._total_requests: int = 0

    @staticmethod
    def _make_safe_url(urls: str | List[str]) -> List[str]:
        # Safe characters from https://stackoverflow.com/questions/695438
        safe = "&$+,/:;=?@#"
        if isinstance(urls, str):
            return [urllib.parse.quote(urls, safe=safe)]
        return [urllib.parse.quote(url, safe=safe) for url in urls]

    @contextlib.contextmanager
    def _event_loop(self) -> asyncio.AbstractEventLoop:
        yield self._loop

    def _log_on_complete_callback(self, *, cached: bool):
        self._current_requests += 1
        ending = "with cache" if cached else "without cache"
        logger.debug(f"Finished {self._current_requests:>{len(str(self._total_requests))}} of {self._total_requests} ({ending})")

    async def _do_get(self, url: str, headers: dict, extensions: dict, log_on_complete: bool) -> bytes:
        try:
            async with self._transport:
                response: httpx.Response = await self._client.get(url, headers=headers, timeout=60, extensions=extensions)
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
            if response.extensions["from_cache"]:
                self._log_on_complete_callback(cached=True)
            else:
                self._log_on_complete_callback(cached=False)

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
        extensions = extensions or {}
        extensions["cache_disabled"] = temp_disable_cache

        responses: list[bytes] = []
        tasks = [self._do_get(url=url, headers=headers, extensions=extensions, log_on_complete=log_on_complete) for url in urls]
        chunks = [tasks[i : i + self._requests_per_second] for i in range(0, len(urls), self._requests_per_second)]
        with self._event_loop():
            # Send requests in groups of `requests_per_second` to not overload remote server
            for chunk in chunks:
                responses += self._loop.run_until_complete(asyncio.gather(*chunk))

        return responses


if __name__ == "__main__":
    x = FastHTTP(cache=True, max_requests_per_second=1)
    x._get(["https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestApi.json?method=getoutputsforinput&input=ensemblgeneid"])
