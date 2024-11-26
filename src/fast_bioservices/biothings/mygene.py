from __future__ import annotations

import json
from typing import NamedTuple

from fast_bioservices.biothings import BioThings
from fast_bioservices.common import Taxon, validate_taxon_id


class _RequestData(NamedTuple):
    taxon_id: int
    chunks: list[list[str]]


class MyGene(BioThings):
    def __init__(self, cache: bool = True):
        """Initiate connection to MyGene.info.

        :param cache: Should cache be used
        """
        self._base_url: str = "https://mygene.info/v3"
        super().__init__(cache=cache)

    async def __setup_requests(self, ids: str | list[str], taxon: int | str | Taxon) -> _RequestData:
        taxon_id = await validate_taxon_id(taxon)
        ids = [ids] if isinstance(ids, str) else ids
        chunks = [ids[i : i + self._chunk_size] for i in range(0, len(ids), self._chunk_size)]
        return _RequestData(taxon_id=taxon_id, chunks=chunks)

    async def gene(self, ids: str | list[str], taxon: int | str | Taxon) -> list[dict]:
        """Obtain ensembl or entrez gene info.

        :param ids: Entrez or Ensembl IDs
        :param taxon: The NCBI Taxonomy ID to use
        :return:
        """
        setup = await self.__setup_requests(ids, taxon)
        url = f"{self._base_url}/gene?species={setup.taxon_id}"
        data = [json.dumps({"ids": chunk}) for chunk in setup.chunks]
        responses = await self._post(url, data=data, headers={"Content-type": "application/json"})
        results = []
        for response in responses:
            results.extend(json.loads(response))
        return results

    async def query(
        self,
        items: list[str],
        taxon: int | str | Taxon,
        scopes: str | list[str] | None = None,
        ensembl_only: bool = False,
        entrez_only: bool = False,
    ) -> list[dict]:
        """Obtain unknown gene data.

        :param items: The items to obtain information for
        :param taxon: The taxon to obtain information for
        :param scopes: The fields to query against. Descriptions can be found at https://docs.mygene.info/en/latest/doc/data.html#available-fields
        :param ensembl_only: Only return Ensembl IDs
        :param entrez_only: Only return Entrez IDs
        :return: A list of dictionaries
        """
        if ensembl_only and entrez_only:
            raise ValueError("Cannot specify both `ensembl_only` and `entrez_only` as True")

        setup = await self.__setup_requests(items, taxon)
        scopes = [scopes] if isinstance(scopes, str) else scopes

        url = f"{self._base_url}/query?species={setup.taxon_id}&size={self._chunk_size}&fields=all&dotfield=true"
        url += "" if scopes is None else f"&scopes={','.join(scopes)}"
        data = [json.dumps({"q": chunk}) for chunk in setup.chunks]
        responses = await self._post(url, data=data, headers={"Content-type": "application/json"})
        results = []
        for r in responses:
            results.extend(json.loads(r))
        return results

    async def metadata(self):
        """Obtain metadata information."""
        raise NotImplementedError("Not implemented yet")


async def _main():
    pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
