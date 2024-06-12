import json
import time
import urllib
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC
from http.client import HTTPResponse
from typing import Optional

from fast_bioservices.log import logger
from fast_bioservices.settings import cache_name


class Response:
    def __init__(self, response: HTTPResponse) -> None:
        self._response: HTTPResponse = response

    @property
    def bytes(self) -> bytes:
        return self._response.read()

    @property
    def text(self) -> str:
        return self.bytes.decode()

    @property
    def json(self) -> dict:
        return json.loads(self.text)


class FastHTTP(ABC):
    _cache: Optional[bool] = None

    def __init__(
        self,
        cache: bool,
        max_requests_per_second: Optional[int] = None,
    ) -> None:
        self._use_cache: bool = cache
        self._max_requests_per_second: int = int(1e10)
        if max_requests_per_second is not None:
            self._max_requests_per_second = max_requests_per_second

        self._requests_made: int = 0
        self._last_request_time: float = 0

    def _get(
        self,
        url: str,
        temp_disable_cache: bool = False,
    ) -> Response:
        parts = urllib.parse.urlparse(url)
        url = urllib.parse.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
        logger.debug(f"Getting {url}")

        # Perform rate limiting
        time_since_last_request = time.time() - self._last_request_time
        if time_since_last_request < 1 / self._max_requests_per_second:
            time.sleep(1 / self._max_requests_per_second - time_since_last_request)
        self._last_request_time = time.time()

        # TODO: Implement caching
        try:
            response: HTTPResponse = urllib.request.urlopen(url)
        except urllib.error.URLError as e:
            logger.error(f"Could not connect to {parts.netloc + parts.path}")
            raise e
        return Response(response)


if __name__ == "__main__":
    http = FastHTTP(cache=True)
