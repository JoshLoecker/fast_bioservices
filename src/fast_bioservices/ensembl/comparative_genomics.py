from __future__ import annotations

from dataclasses import dataclass
import json
from typing import List, Literal

from fast_bioservices.ensembl.ensembl import Ensembl
from fast_bioservices.settings import default_workers


@dataclass
class HomologyTarget:
    protein_id: str
    cigar_line: str
    taxon_id: int
    species: str
    align_seq: str
    id: str
    perc_pos: float
    perc_id: float


@dataclass
class HomologySource:
    align_seq: str
    cigar_line: str
    protein_id: str
    species: str
    taxon_id: int
    perc_pos: float
    perc_id: float
    id: str


@dataclass
class HomologyResult:
    id: str
    method_link_type: str
    taxonomy_level: str
    dn_ds: str
    target: HomologyTarget
    type: str
    source: HomologySource


class GetCafeTree(Ensembl):
    def __init__(self, *, max_workers: int = default_workers, cache: bool = True):
        super().__init__(max_workers=max_workers, cache=cache)
        raise NotImplementedError("Not implemented yet")


class GetGeneTree(Ensembl):
    def __init__(self, *, max_workers: int = default_workers, cache: bool = True):
        super().__init__(max_workers=max_workers, cache=cache)
        raise NotImplementedError("Not implemented yet")


class GetAlignment(Ensembl):
    def __init__(self, *, max_workers: int = default_workers, cache: bool = True):
        super().__init__(max_workers=max_workers, cache=cache)
        raise NotImplementedError("Not implemented yet")


class GetHomology(Ensembl):
    def __init__(self, max_workers: int = 4, cache: bool = True):
        self._max_workers: int = max_workers

        super().__init__(max_workers=self._max_workers, cache=cache)

    @property
    def url(self) -> str:
        return self._url

    def by_species_with_symbol_or_id(
        self,
        reference_species: str,
        ensembl_id_or_symbol: str | List[str],
        aligned: bool = True,
        cigar_line: bool = True,
        compara: str = "vertebrates",
        external_db: str = "",
        format: Literal["full", "condensed"] = "full",
        sequence: Literal["none", "cdna", "protein"] = "protein",
        target_species: str = "",
        target_taxon: int | None = None,
        type: Literal["orthologues", "paralogues", "projections", "all"] = "all",
    ) -> List[HomologyResult]:
        ensembl_id_or_symbol = [ensembl_id_or_symbol] if isinstance(ensembl_id_or_symbol, str) else ensembl_id_or_symbol

        urls = []
        for e_id in ensembl_id_or_symbol:
            path = f"/homology/symbol/{reference_species}/{e_id}?"
            if e_id.startswith("ENSG"):
                path = path.replace("/symbol/", "/id/")
            path += f"compara={compara};format={format};sequence={sequence};type={type}"

            if aligned:
                path += ";aligned"
            if cigar_line:
                path += ";cigar_line"
            if external_db != "":
                path += f";external_db={external_db}"
            if target_species != "":
                path += f";target_species={target_species}"
            if target_taxon is not None:
                path += f";target_taxon={target_taxon}"
            urls.append(self._url + path)

        homology_results: list[HomologyResult] = []
        results = self._get(
            urls=urls,
            headers={"Content-Type": "application/json"},
        )
        for result in results:
            as_json = json.loads(result)
            id_ = as_json["data"][0]["id"]
            homologies: list = as_json["data"][0]["homologies"]

            for homology in homologies:
                source = HomologySource(**homology["source"])
                target = HomologyTarget(**homology["target"])
                result = HomologyResult(
                    id=id_,
                    method_link_type=homology["method_link_type"],
                    taxonomy_level=homology["taxonomy_level"],
                    dn_ds=homology["dn_ds"],
                    type=homology["type"],
                    target=target,
                    source=source,
                )
                homology_results.append(result)
        return homology_results


def main():
    e = GetHomology(max_workers=1, cache=False)
    e.by_species_with_symbol_or_id(
        reference_species="human",
        ensembl_id_or_symbol="ENSG00000157764",
        target_species="macaca_mulatta",
    )


if __name__ == "__main__":
    main()
