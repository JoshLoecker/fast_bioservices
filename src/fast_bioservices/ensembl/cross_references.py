from dataclasses import dataclass
from typing import List, Literal, Optional, Union

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
    def __init__(
        self,
        max_workers: int = 4,
        show_progress: bool = True,
        cache: bool = True,
    ):
        self._max_workers: int = max_workers
        self._show_progress: bool = show_progress

        super().__init__(
            max_workers=self._max_workers,
            show_progress=self._show_progress,
            cache=cache,
        )

    def get_ensembl_from_external(
        self,
        species: str,
        gene_symbols: Union[str, List[str]],
        db_type: Literal["core"] = "core",
        external_db_filter: Optional[str] = None,
        feature_filter: Optional[str] = None,
    ):
        validate_species: Optional[Species] = self._match_species(species)
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
            as_json = result.json[0]
            references.append(EnsemblReference(**as_json, input=gene_symbols[i]))
        return references

    def get_external_from_ensembl(
        self,
        ensembl_id: Union[str, List[str]],
        db_type: Literal["core"] = "core",
        all_levels: bool = False,
        external_db_filter: Optional[str] = None,
        feature_filter: Optional[str] = None,
        species: Optional[str] = None,
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
            as_json = result.json[0]
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
