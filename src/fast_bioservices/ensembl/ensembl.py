from dataclasses import dataclass
from typing import List, Optional

from fast_bioservices._base import BaseModel
from fast_bioservices._fast_http import FastHTTP
from fast_bioservices._utils import fuzzy_search


@dataclass
class Species:
    strain_collection: str
    aliases: list[str]
    name: str
    taxon_id: int
    assembly: str
    common_name: str
    groups: list[str]
    accession: str
    release: int
    division: str
    strain: str
    display_name: str


class Ensembl(BaseModel, FastHTTP):
    def __init__(
        self,
        max_workers: int,
        show_progress: bool,
        cache: bool = True,
    ):
        self._url = "https://rest.ensembl.org"
        BaseModel.__init__(self, url=self._url)
        FastHTTP.__init__(
            self,
            cache=cache,
            workers=max_workers,
            max_requests_per_second=15,
            show_progress=show_progress,
        )

    @property
    def url(self) -> str:
        return self._url

    def _get_species(self) -> List[Species]:
        path = self._url + "/info/species"
        response = self._get(path, headers={"Content-Type": "application/json"})
        species: list[Species] = []
        for item in response[0].json["species"]:
            species.append(Species(**item))
        return species

    def _match_species(self, species: str) -> Optional[Species]:
        """
        This function will make sure the user enters a valid species name
        It will do this by collecting all the species names from the Ensembl API
        Then doing a fuzzy search on the species name
        If the species name does not exactly match an alias from the API,
        it will show a warning so the user knows they have not perfectly matched a species name

        Parameters
        ----------
        species : str
            The species to validate

        Returns
        -------
        Species
            The species object from the Ensembl API
        """
        species = species.lower()
        species_list = self._get_species()
        matches: list[list[str]] = []
        for possible_matches in species_list:
            result = 
            matches.append(f)
        print(matches)
        return None


def main():
    e = Ensembl(max_workers=1, show_progress=True)
    e._match_species("homo_sapien")


if __name__ == "__main__":
    main()