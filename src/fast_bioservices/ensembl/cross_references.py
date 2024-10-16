from __future__ import annotations

from dataclasses import dataclass
import json
from typing import List, Literal

from fast_bioservices.ensembl.ensembl import Ensembl, Species
from fast_bioservices.settings import default_workers


@dataclass(frozen=True)
class EnsemblReference:
    input: str
    type: str
    id: str


@dataclass(frozen=True)
class ExternalReference:
    description: str
    info_text: str
    synonyms: List[str]
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
    def __init__(self, max_workers: int = default_workers, cache: bool = True):
        self._max_workers: int = max_workers

        super().__init__(max_workers=self._max_workers, cache=cache)

    def get_ensembl_from_external(
        self,
        species: str,
        gene_symbols: str | List[str],
        db_type: Literal["core"] = "core",
        external_db_filter: str | None = None,
        feature_filter: str | None = None,
    ):
        validate_species: Species | None = self._match_species(species)
        assert validate_species is not None, f"Species {species} not found"

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
        for i, result in enumerate(self._get(urls=urls, headers={"Content-Type": "application/json"})):
            as_json = json.loads(result.decode())[0]
            references.append(EnsemblReference(**as_json, input=gene_symbols[i]))
        return references

    def get_external_from_ensembl(
        self,
        ensembl_id: str | List[str],
        db_type: Literal["core"] = "core",
        all_levels: bool = False,
        external_db_filter: str | None = None,
        feature_filter: str | None = None,
        species: str | None = None,
    ) -> List[ExternalReference]:
        ensembl_id = [ensembl_id] if isinstance(ensembl_id, str) else ensembl_id

        urls = []
        for e_id in ensembl_id:
            path = f"/xrefs/id/{e_id}?db_type={db_type}"
            if all_levels:
                path += ";all_levels=1"
            if external_db_filter:
                path += f";external_db={external_db_filter}"
            if feature_filter:
                path += f";object_type={feature_filter}"
            if species:
                path += f";species={species}"
            urls.append(self._url + path)

        references: list[ExternalReference] = []
        for result in self._get(urls=urls, headers={"Content-Type": "application/json"}):
            as_json = json.loads(result.decode())[0]
            references.append(ExternalReference(**as_json))

        return references

    @property
    def url(self) -> str:
        return self._url


def main():
    c = CrossReference(max_workers=1)

    r = c.get_ensembl_from_external("human", ["GOLT1A", "GOLT1B"])
    print(r)


if __name__ == "__main__":
    main()
