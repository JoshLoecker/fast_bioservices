from __future__ import annotations

import json
from functools import lru_cache

from fast_bioservices.common import Taxon
from fast_bioservices.ensembl.cross_references import CrossReference
from fast_bioservices.fast_http import _AsyncHTTPClient

__all__ = ["CrossReference"]
# __all__ = ["GetAlignment", "GetCafeTree", "GetGeneTree", "GetHomology", "HomologyResult", "CrossReference"]


@lru_cache
async def get_valid_ensembl_species(value: int | str | Taxon):
    client = _AsyncHTTPClient(cache=False, max_requests_per_second=1)
    ensembl_species = (
        await client._get(
            "https://rest.ensembl.org/info/species",
            headers={"Content-Type": "application/json"},
            log_on_complete=False,
        )
    )[0]

    """
    {
        'display_name': 'Huchen',
        'strain_collection': None,
        'assembly': 'ASM331708v1',
        'name': 'hucho_hucho',
        'common_name': 'huchen',
        'strain': None,
        'taxon_id': '62062',
        'release': 113,
        'division': 'EnsemblVertebrates',
        'accession': 'GCA_003317085.1',
        'aliases': [],
        'groups': ['core', 'rnaseq']
    }
    """

    for species in json.loads(ensembl_species)["species"]:
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
