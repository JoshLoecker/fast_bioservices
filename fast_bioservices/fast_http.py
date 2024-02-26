import urllib.parse
from typing import Optional, Union

import modguard
import requests
import requests.utils
import requests_cache

from fast_bioservices.log import logger
from fast_bioservices.settings import cache_name


class HTTP:
    _cache: Optional[bool] = None
    _session: requests_cache.CachedSession = None
    warned: bool = False

    def __init__(self, cache: bool) -> None:
        self._use_cache: bool = cache

        if HTTP._session is None:
            HTTP._session = requests_cache.CachedSession(cache_name=cache_name)
            if not self._use_cache:
                HTTP._session.settings.disabled = True
        self._session = HTTP._session

    def _get(
        self, url, _internal_check: bool = None
    ) -> Union[requests.Response, requests.exceptions.ConnectionError]:
        parts = urllib.parse.urlparse(url)
        url = requests.utils.requote_uri(url)
        logger.debug(f"Getting {url}")

        try:
            if _internal_check:
                self._session.settings.disabled = True
                response = self._session.get(url)
                self._session.settings.disabled = False
            else:
                response = self._session.get(url)
        except requests.exceptions.ConnectionError as e:
            if not self.warned:
                logger.error(f"Could not connect to {parts.netloc + parts.path}")
                self.warned = True
            return e
        return response

    def _get_internal_json(self, url) -> dict:
        return self._get(url, _internal_check=True).json()

    def _get_internal_text(self, url) -> str:
        return self._get(url, _internal_check=True).text

    @modguard.public(allowlist=["fast_bioservices.biodbnet"])
    def get_json(self, url) -> dict:
        return self._get(url, _internal_check=False).json()

    @modguard.public(allowlist=["fast_bioservices.biodbnet"])
    def get_text(self, url) -> str:
        return self._get(url, _internal_check=False).text


if __name__ == "__main__":
    http = HTTP(cache=True)
