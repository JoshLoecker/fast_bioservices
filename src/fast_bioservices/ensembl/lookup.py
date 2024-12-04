from __future__ import annotations

import json
from typing import Literal

from fast_bioservices.common import Taxon
from fast_bioservices.common.ensembl import get_valid_ensembl_species
from fast_bioservices.ensembl import Ensembl


class Lookup(Ensembl):
    def __init__(self, cache: bool = True):
        """Access ensembl data using Ensembl IDs or Gene Symbols."""
        self._base: str = "https://rest.ensembl.org"
        self._cache: bool = cache
        self._max_requests_per_second: int = 12

        super().__init__(cache=cache)

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
        """Access information by ensembl ID."""
        url = f"{self._base}/lookup/id"
        ensembl_ids = [ensembl_ids] if isinstance(ensembl_ids, str) else ensembl_ids
        return await self._process(url=url, as_type="ids", items=ensembl_ids)

    async def by_symbol(self, symbols: str | list[str], species: int | str | Taxon) -> list[dict]:
        """Access data by Gene Symbol."""
        ensembl_taxon = await get_valid_ensembl_species(species)
        url = f"{self._base}/lookup/symbol/{ensembl_taxon}"
        symbols = [symbols] if isinstance(symbols, str) else symbols
        return await self._process(url=url, as_type="symbols", items=symbols)
