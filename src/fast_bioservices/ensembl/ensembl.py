import json
from dataclasses import dataclass
from typing import List, Optional

from fast_bioservices.fast_http import _AsyncHTTPClient
from fast_bioservices.utils import fuzzy_search


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


@dataclass
class FuzzyResult:
    species: Species
    score: float


class Ensembl(_AsyncHTTPClient):
    def __init__(self, cache: bool = True):
        self._url = "https://rest.ensembl.org"
        _AsyncHTTPClient.__init__(self, cache=cache, max_requests_per_second=15)

    @property
    def url(self) -> str:
        return self._url

    def __get_species(self) -> List[Species]:
        path = f"{self._url}/info/species"
        response = self._get(path, headers={"Content-Type": "application/json"})
        species: list[Species] = []
        as_json = json.loads(response[0].decode())
        species.extend(Species(**item) for item in as_json["species"])
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
        species_list = self.__get_species()

        matches: list[FuzzyResult] = []
        for possible_matches in species_list:
            score = fuzzy_search(query=species, possibilities=possible_matches.aliases)
            matches.append(FuzzyResult(possible_matches, score))

        if not matches:
            return None
        highest_match = max(matches, key=lambda x: x.score)
        return highest_match.species


def main():
    e = Ensembl()
    e._match_species("human")


if __name__ == "__main__":
    main()
