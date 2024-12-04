from __future__ import annotations

from fast_bioservices.fast_http import _AsyncHTTPClient


class BioThings(_AsyncHTTPClient):
    def __init__(self, cache: bool):
        self._chunk_size: int = 1000
        super().__init__(cache=cache, max_requests_per_second=5)

    async def _post(self, url, **kwargs) -> list[bytes]:
        url += "&email=joshloecker@icloud.com"
        return await super()._post(url, **kwargs)
