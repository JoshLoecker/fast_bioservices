import os
from typing import Union

import appdirs
import requests
import requests.utils
import requests_cache

from fast_bioservices.log import logger


def flatten(lists: list) -> list:
    data = []
    for item in lists:
        if isinstance(item, list):
            data.extend(flatten(item))
        else:
            data.append(item)
    return data


class HTTP:
    _session: Union[requests_cache.CachedSession, requests.Session] = None
    
    def __init__(self, cache: bool) -> None:
        self._use_cache: bool = cache
        if self._use_cache:
            if HTTP._session is None:
                _db_path: str = os.path.join(appdirs.user_cache_dir("fast_biodbnet"), "cache.sqlite")
                if not os.path.exists(os.path.dirname(_db_path)):
                    logger.debug(f"Creating cache at {_db_path}")
                    os.makedirs(os.path.dirname(_db_path), exist_ok=True)
                HTTP._session = requests_cache.CachedSession(
                    cache_name=_db_path,
                    backend="sqlite",
                    serializer="pickle"
                )
        else:
            if HTTP._session is None:
                HTTP._session = requests.session()
        self._session = HTTP._session
    
    def _get(self, url) -> requests.Response:
        url = requests.utils.requote_uri(url)
        logger.debug(f"Getting {url}")
        response = self._session.get(url)
        return response
    
    def get_json(self, url) -> dict:
        return self._get(url).json()
    
    def get_text(self, url) -> str:
        return self._get(url).text
