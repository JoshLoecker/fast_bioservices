import urllib
import urllib.parse
import urllib.request
from optparse import Option
from typing import List, Optional, Union

import httpx
import httpx_cache
import modguard

from fast_bioservices.log import logger
from fast_bioservices.settings import cache_name


class HTTP:
    _cache: Optional[bool] = None
    _client: httpx_cache.Client = httpx_cache.Client(
        cache=httpx_cache.FileCache(cache_name),
        timeout=30,
    )
    warned: bool = False

    def __init__(
        self,
        cache: bool,
        max_requests_per_second: Optional[int] = None,
    ) -> None:
        self._use_cache: bool = cache
        self._max_requests_per_second: int = (
            int(1e10) if max_requests_per_second is None else max_requests_per_second
        )

        if not self._use_cache:
            HTTP._client.headers["cache-control"] = "no-cache"
        self._client = HTTP._client

    def _get(
        self,
        url,
        _internal_check: Optional[bool] = None,
    ) -> httpx.Response:
        parts = urllib.parse.urlparse(url)
        url = urllib.parse.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
        logger.debug(f"Getting {url}")

        try:
            if _internal_check:
                if self._use_cache:
                    self._client.headers["cache-control"] = "no-cache"
                    response = self._client.get(url)
                    self._client.headers.pop("cache-control")
                else:
                    response = self._client.get(url)
            else:
                response = self._client.get(url)
        except httpx.ConnectError as e:
            if not self.warned:
                logger.error(f"Could not connect to {parts.netloc + parts.path}")
                self.warned = True
            raise e
        return response

    def _get_internal_json(self, url) -> dict:
        return self._get(url, _internal_check=True).json()

    def _get_internal_text(self, url) -> str:
        return self._get(url, _internal_check=True).text

    @modguard.public(allowlist=["fast_bioservices.biodbnet"])
    def get_json(self, url) -> Union[dict, List[dict]]:
        return self._get(url, _internal_check=False).json()

    @modguard.public(allowlist=["fast_bioservices.biodbnet"])
    def get_text(self, url) -> str:
        return self._get(url, _internal_check=False).text


if __name__ == "__main__":
    http = HTTP(cache=True)
