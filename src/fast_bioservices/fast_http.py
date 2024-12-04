from __future__ import annotations

import asyncio
import sys
import time
import urllib.parse
from typing import Literal, NamedTuple

import hishel
import httpcore
import httpx
from hishel._utils import generate_key
from httpx import Request, Response
from loguru import logger

from fast_bioservices.settings import cache_dir


class RequestSetup(NamedTuple):
    urls: list[str]
    headers: dict
    extensions: dict


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

    prefix = key[:2]
    key_dir = cache_dir / prefix
    key_dir.mkdir(parents=True, exist_ok=True)

    return f"{prefix}/{method}|{host}|{key}"


def _make_safe_url(urls: str | list[str]) -> str | list[str]:
    safe_chars = "&$+,/:;=?@#"
    if isinstance(urls, str):
        return urllib.parse.quote(urls, safe=safe_chars)
    return sorted(urllib.parse.quote(url, safe=safe_chars) for url in urls)


class _AsyncRateLimitTransport(httpx.AsyncBaseTransport):
    """Implement rate limiting on httpx transports."""

    def __init__(self, rate: int | float, period: int = 1):
        self.transport = httpx.AsyncHTTPTransport()
        self.rate = rate  # Requests per second
        self.period = period
        self.last_reset = time.time()
        self.requests_in_period = 0

    async def handle_async_request(self, request: Request) -> Response:
        now = time.time()
        if now - self.last_reset >= self.period:  # We've waited for `period` seconds since last reset, reset counter
            self.last_reset = now
            self.requests_in_period = 0

        while self.requests_in_period >= self.rate:  # We've hit the rate limit, sleep
            logger.trace(f"Sleeping for {1 / self.rate} seconds")
            await asyncio.sleep(1 / self.rate)
            now = time.time()
            if now - self.last_reset >= self.period:  # Make sure that we've waited long enough
                self.last_reset = now
                self.requests_in_period = 0
                break

        self.requests_in_period += 1
        return await self.transport.handle_async_request(request)


class _AsyncHTTPClient:
    def __init__(self, *, cache: bool, max_requests_per_second) -> None:
        self._use_cache: bool = cache
        transport = _AsyncRateLimitTransport(rate=max_requests_per_second)
        if self._use_cache:
            self._storage = hishel.AsyncFileStorage(base_path=cache_dir, ttl=sys.maxsize)
            self._controller = hishel.Controller(
                key_generator=_key_generator,
                allow_stale=True,
                force_cache=True,
                cacheable_methods=["GET", "POST", "HEAD"],
            )
            self._transport = hishel.AsyncCacheTransport(
                transport=transport,
                storage=self._storage,
                controller=self._controller,
            )
        else:
            self._transport = transport
        self._client: httpx.AsyncClient = httpx.AsyncClient(transport=self._transport, timeout=180)

        self._semaphore = asyncio.Semaphore(value=5)
        self.__current_requests: int = 0
        self.__total_requests: int = 0
        self.__log_per_step: int = 1
        self.__working_time: float = 0.0
        self.__chunk_time: float = 0.0
        self.__padding: int = 0

    def update_rate_limit(self, value: int):
        self._transport.rate = value

    def _log_callback(self, *, cached: bool):
        self.__current_requests += 1

        if self.__current_requests % self.__log_per_step == 0 or self.__current_requests == self.__total_requests:
            current_time = time.time()
            working_time = round(current_time - self.__working_time, 1)
            chunk_time = round(current_time - self.__chunk_time, 1)
            ending = "with cache" if cached else "without cache"
            logger.debug(
                f"Finished {self.__current_requests:>{self.__padding}} of {self.__total_requests} ({ending})"
                f" - chunk took {chunk_time} seconds"
                f" - running for {working_time} seconds"
            )
            self.__chunk_time = current_time

    async def __perform_action(self, func: Literal["get", "post"], url: str, /, log_on_complete: bool, **kwargs):
        try:
            response: httpx.Response
            async with self._transport, self._semaphore:
                if func == "get":
                    response = await self._client.get(url, **kwargs)
                elif func == "post":
                    response = await self._client.post(url, **kwargs)
        except httpx.ReadTimeout as e:
            logger.critical(f"ReadTimeout: Timed out while receiving data from the host: {url}")
            raise e from httpx.ReadTimeout
        except httpx.ConnectTimeout as e:
            logger.critical(f"ConnectTimeout: Timed out while connecting to the host: {url}")
            raise e from httpx.ConnectTimeout
        except httpx.ConnectError as e:
            logger.critical(f"ConnectError: Failed to establish a connection: {url}")
            raise e from httpx.ConnectError

        if log_on_complete:
            if response.extensions.get("from_cache"):
                self._log_callback(cached=True)
            else:
                self._log_callback(cached=False)
        return response.content

    def _setup_action(self) -> None:
        # Show update every 10% with a minimum of every 1000
        self.__padding = len(str(self.__total_requests))

        self.__working_time = time.time()
        self.__chunk_time = time.time()

        self.__log_per_step = int(self.__total_requests * 0.1)
        if self.__log_per_step < 1:
            self.__log_per_step = 1
        self.__log_per_step = min(1000, self.__log_per_step)
        logger.debug(f"Will show progress every {self.__log_per_step} steps ({self.__total_requests} total steps)")

    async def _get(
        self,
        urls: str | list[str],
        headers: dict | None = None,
        temp_disable_cache: bool = False,
        log_on_complete: bool = True,
        extensions: dict | None = None,
    ) -> list[bytes]:
        # Make urls safe
        # Safe characters from https://stackoverflow.com/questions/695438
        urls: list[str] = [_make_safe_url(urls)] if isinstance(urls, str) else _make_safe_url(urls)
        self.__current_requests = 0
        self.__total_requests = len(urls)
        headers = headers or {}
        extensions = extensions or {}
        extensions["cache_disabled"] = temp_disable_cache
        self._setup_action()

        responses: list[bytes] = await asyncio.gather(
            *[
                self.__perform_action("get", url, log_on_complete, headers=headers, extensions=extensions)
                for url in urls
            ]
        )
        return responses

    async def _post(
        self,
        url: str,
        *,
        data: str | list[str],
        headers: dict | None = None,
        temp_disable_cache: bool = False,
        log_on_complete: bool = True,
        extensions: dict | None = None,
    ) -> list[bytes]:
        url: str = _make_safe_url(url)
        self.__current_requests = 0
        self.__total_requests = 1 if isinstance(data, str) else len(data)
        headers = headers or {}
        extensions = extensions or {}
        extensions["cache_disabled"] = temp_disable_cache
        self._setup_action()

        responses: list[bytes]
        if isinstance(data, list):
            responses = await asyncio.gather(
                *[
                    self.__perform_action(
                        "post", url, log_on_complete, data=chunk, headers=headers, extensions=extensions
                    )
                    for chunk in data
                ]
            )
        else:
            responses = [
                await self.__perform_action(
                    "post", url, log_on_complete, data=data, headers=headers, extensions=extensions
                )
            ]

        return responses
