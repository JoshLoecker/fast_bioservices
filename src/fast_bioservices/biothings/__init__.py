from __future__ import annotations

from fast_bioservices.fast_http import _AsyncHTTPClient


class BioThings(_AsyncHTTPClient):
    async def _post(self, url, **kwargs) -> list[bytes]:
        url += "&email=joshloecker.com"
        return await super()._post(url, **kwargs)
