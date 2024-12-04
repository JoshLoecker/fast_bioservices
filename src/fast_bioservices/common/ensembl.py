from __future__ import annotations

from functools import cache

import httpx

from fast_bioservices.common import Taxon


@cache
async def get_valid_ensembl_species(value: int | str | Taxon):
    """Determine if the input is a valid Ensembl species."""
    taxon_value = str(value.value) if isinstance(value, Taxon) else str(value)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://rest.ensembl.org/info/species", headers={"Content-Type": "application/json"}
        )

        for species in response.json()["species"]:
            if taxon_value in {
                species["display_name"],
                species["name"],
                species["common_name"],
                species["taxon_id"],
                species["assembly"],
                species["accession"],
            }:
                return species["name"]
        raise ValueError(
            f"{taxon_value} is not a valid ensembl species. "
            f"Visit https://www.ensembl.org to get a valid species identifier"
        )


async def _main():
    await get_valid_ensembl_species("mouse")


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
