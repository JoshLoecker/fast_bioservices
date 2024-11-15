from __future__ import annotations

from functools import lru_cache

import httpx

from fast_bioservices.common import Taxon


@lru_cache
async def get_valid_ensembl_species(value: int | str | Taxon):
    async with httpx.AsyncClient() as client:
        async with client.get("https://rest.ensembl.org/info/species", headers={"Content-Type": "application/json"}) as response:
            for species in response.json()["species"]:
                # for species in json.loads(response.)["species"]:
                if value in {
                    species["display_name"],
                    species["name"],
                    species["common_name"],
                    species["taxon_id"],
                    species["assembly"],
                    species["accession"],
                }:
                    return species["name"]
            raise ValueError(f"{value} is not a valid ensembl species. Visit https://www.ensembl.org to get a valid species identifier")


async def _main():
    await get_valid_ensembl_species("mouse")


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
