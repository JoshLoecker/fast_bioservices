from __future__ import annotations

import json
from typing import Literal

from fast_bioservices.fast_http import _AsyncHTTPClient


class Lookup(_AsyncHTTPClient):
    def __init__(self, cache: bool = True):
        self._base: str = "https://rest.ensembl.org"
        self._cache: bool = cache
        self._max_requests_per_second: int = 12

        super().__init__(cache=cache, max_requests_per_second=self._max_requests_per_second)

    async def _process(self, *, url: str, as_type: Literal["ids", "symbols"], items: list[str]) -> list[dict]:
        response = (
            await self._post(
                url,
                data=json.dumps({as_type: items}),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
        )[0]
        as_json = json.loads(response)
        return list(as_json.values())

    async def by_ensembl(self, ensembl_ids: str | list[str]) -> list[dict]:
        url = f"{self._base}/lookup/id"
        ensembl_ids = [ensembl_ids] if isinstance(ensembl_ids, str) else ensembl_ids
        return await self._process(url=url, as_type="ids", items=ensembl_ids)

    async def by_symbol(self, symbols: str | list[str], species: str) -> list[dict]:
        url = f"{self._base}/lookup/symbol/{species}"
        symbols = [symbols] if isinstance(symbols, str) else symbols
        return await self._process(url=url, as_type="symbols", items=symbols)


async def _main():
    e = Lookup(cache=False)
    print(await e.by_ensembl(["ENSG00000157764", "ENSG00000157765"]))
    print(await e.by_ensembl(["ENSG00000157764"]))
    print(await e.by_symbol(["GNAS", "HBA1", "HBA2"], species="homo_sapiens"))
    print(await e.by_symbol(["GNAS"], species="homo_sapiens"))


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
