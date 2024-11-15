from __future__ import annotations

import json

from fast_bioservices.common import Taxon, validate_taxon_id
from fast_bioservices.fast_http import _AsyncHTTPClient


class MyGene(_AsyncHTTPClient):
    def __init__(self, cache: bool = True):
        self._base_url: str = "https://mygene.info/v3"
        self._chunk_size: int = 1000
        super().__init__(cache=cache, max_requests_per_second=5)

    async def gene(self, ids: str | list[str], taxon: int | str | Taxon) -> list[dict]:
        """
        :param ids: Entrez or Ensembl IDs
        :param taxon: The NCBI Taxonomy ID to use
        :return:
        """
        taxon_id = await validate_taxon_id(taxon)
        ids = [ids] if isinstance(ids, str) else ids
        url = f"{self._base_url}/gene?species={taxon_id}"
        chunks = [ids[i : i + self._chunk_size] for i in range(0, len(ids), self._chunk_size)]
        data = [json.dumps({"ids": chunk}) for chunk in chunks]
        responses = await self._post(url, data=data, headers={"Content-type": "application/json"})
        results = []
        for response in responses:
            results.extend(json.loads(response))
        return results

    async def query(self):
        raise NotImplementedError("Not implemented yet")

    async def metadata(self):
        raise NotImplementedError("Not implemented yet")


async def _main():
    m = MyGene()
    r = await m.gene(["ENSG00000170558", "ENSG00000153563"], taxon=Taxon.HOMO_SAPIENS)
    print(r)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
