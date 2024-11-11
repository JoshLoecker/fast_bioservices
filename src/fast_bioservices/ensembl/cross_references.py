from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from fast_bioservices.ensembl.ensembl import Ensembl, Species


@dataclass(frozen=True)
class EnsemblReference:
    input: str
    type: str
    id: str


@dataclass(frozen=True)
class ExternalReference:
    description: str
    info_text: str
    synonyms: list[str]
    dbname: str
    info_type: str
    db_display_name: str
    display_id: str
    version: str
    primary_id: str

    def __post_init__(self):
        if object.__getattribute__(self, "description") is None:
            object.__setattr__(self, "description", "")


class CrossReference(Ensembl):
    def __init__(self, cache: bool = True):
        super().__init__(cache=cache)

    async def by_external(
        self,
        species: str,
        gene_symbols: str | list[str],
        db_type: Literal["core"] = "core",
        external_db_filter: str | None = None,
        feature_filter: str | None = None,
    ):
        validate_species: Species | None = self._match_species(species)
        if validate_species is None:
            raise ValueError(f"Species {species} not found")

        gene_symbols = [gene_symbols] if isinstance(gene_symbols, str) else gene_symbols

        urls = []
        for symbol in gene_symbols:
            path = f"/xrefs/symbol/{validate_species.common_name}/{symbol}?db_type={db_type}"
            if external_db_filter:
                path += f";external_db={external_db_filter}"
            if feature_filter:
                path += f";object_type={feature_filter}"
            urls.append(self._url + path)

        references: list[EnsemblReference] = []
        for i, result in enumerate(await self._get(urls=urls, headers={"Content-Type": "application/json"})):
            as_json = json.loads(result.decode())[0]
            references.append(EnsemblReference(**as_json, input=gene_symbols[i]))
        return references

    async def by_ensembl(
        self,
        ids: str | list[str],
        db_type: Literal["core", "otherfeatures"] = "core",
        all_levels: bool = False,
        external_db_filter: str | None = None,
        feature_filter: str | None = None,
        species: str | None = None,
    ) -> dict[str, list[dict]]:
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

        results: dict[str, list[dict]] = {}
        for i, result in enumerate(await self._get(urls=urls, headers={"Content-Type": "application/json"})):
            results[ids[i]] = json.loads(result)
        return results

    @property
    def url(self) -> str:
        return self._url


async def _main():
    c = CrossReference()

    one = await c.by_ensembl(ids=["ENSG00000157764"])
    print(one)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
