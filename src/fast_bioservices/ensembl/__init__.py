from __future__ import annotations

from fast_bioservices.fast_http import _AsyncHTTPClient


class Ensembl(_AsyncHTTPClient):
    def __init__(self, cache: bool = True):
        self._url = "https://rest.ensembl.org"
        _AsyncHTTPClient.__init__(self, cache=cache, max_requests_per_second=12)

    @property
    def url(self) -> str:
        return self._url
