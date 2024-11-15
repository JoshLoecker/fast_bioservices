from __future__ import annotations

import json

from fast_bioservices.fast_http import _AsyncHTTPClient


class MyGene(_AsyncHTTPClient):
    def __init__(self, cache: bool = True):
        self._base_url: str = "https://mygene.info/v3"
        self._chunk_size: int = 1000
        super().__init__(cache=cache, max_requests_per_second=5)

    async def gene(self, ids: str | list[str]) -> list[dict]:
        """
        :param ids: Entrez or Ensembl IDs
        :return:
        """
        ids = [ids] if isinstance(ids, str) else ids
        url = f"{self._base_url}/gene"
        chunks = [ids[i : i + self._chunk_size] for i in range(0, len(ids), self._chunk_size)]

        results: list[dict] = []
        for chunk in chunks:
            response = (await self._post(url, data=json.dumps({"ids": chunk}), headers={"Content-type": "application/json"}))[0]
            results.extend(json.loads(response))
        return results

    async def query(self):
        raise NotImplementedError("Not implemented yet")

    async def metadata(self):
        raise NotImplementedError("Not implemented yet")


async def _main():
    m = MyGene()
    r = await m.gene(["ENSG00000170558", "ENSG00000153563"])
    print(r[0].keys())
    print(r[0]["entrezgene"])
    print(r[0]["ensembl"]["gene"])
    print(r[0]["symbol"])


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
