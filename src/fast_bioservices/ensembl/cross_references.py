from __future__ import annotations

import json
from typing import Literal

from fast_bioservices.common import Taxon
from fast_bioservices.common.ensembl import get_valid_ensembl_species
from fast_bioservices.ensembl import Ensembl


class CrossReference(Ensembl):
    def __init__(self, cache: bool = True):
        """Cross reference data from ensembl and external sources."""
        super().__init__(cache=cache)

    async def by_external(
        self,
        species: int | str | Taxon,
        gene_symbols: str | list[str],
        db_type: Literal["core"] = "core",
        external_db_filter: str | None = None,
        feature_filter: str | None = None,
    ):
        """Collect ensembl-related items from an external database."""
        ensembl_species = await get_valid_ensembl_species(species)
        gene_symbols = [gene_symbols] if isinstance(gene_symbols, str) else gene_symbols

        urls = []
        for symbol in gene_symbols:
            path = f"/xrefs/symbol/{ensembl_species}/{symbol}?db_type={db_type}"
            if external_db_filter:
                path += f";external_db={external_db_filter}"
            if feature_filter:
                path += f";object_type={feature_filter}"
            urls.append(self._url + path)

        references: list[dict] = []
        for result in await self._get(urls=urls, headers={"Content-Type": "application/json"}):
            references.extend(json.loads(result))
        return references

    async def by_ensembl(
        self,
        ids: str | list[str],
        db_type: Literal["core", "otherfeatures"] = "core",
        all_levels: bool = False,
        external_db_filter: str | None = None,
        feature_filter: str | None = None,
        species: str | None = None,
    ) -> dict[str, dict]:
        """Access external items from an ensembl ID."""
        ids = [ids] if isinstance(ids, str) else ids

        urls = []
        for e_id in ids:
            path = f"/xrefs/id/{e_id}?db_type={db_type}"
            if all_levels:
                path += "&all_levels=1"
            if external_db_filter:
                path += f"&external_db={external_db_filter}"
            if feature_filter:
                path += f"&object_type={feature_filter}"
            if species:
                path += f"&species={species}"
            urls.append(self._url + path)

        results: dict[str, dict] = {}
        responses = await self._get(urls=urls, headers={"Content-Type": "application/json"})
        for i, response in enumerate(responses):
            results[ids[i]] = json.loads(response)
        return results

    @property
    def url(self) -> str:
        """Return the root URL."""
        return self._url


async def _main():
    import pandas as pd

    c = CrossReference(cache=False)
    df = pd.read_csv(
        "/Users/joshl/Projects/AcuteRadiationSickness/data/captopril/gene_counts/gene_counts_matrix_full_waterIrradiated24hr.csv"
    )
    ids = df["genes"].tolist()

    await c.by_ensembl(ids=ids)

    # for chunk in range(0, len(ids), 1000):
    #     await c.by_ensembl(ids=ids[chunk : chunk + 1000])
    # convert = await c.by_ensembl(ids=ids)
    # print(convert)
    # print(type(convert))
    # print(len(convert))


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
