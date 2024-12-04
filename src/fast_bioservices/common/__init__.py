from __future__ import annotations

from enum import Enum
from typing import Type, TypeVar

from loguru import logger

T = TypeVar("T", bound=Enum)


class Taxon(Enum):
    ARABIDOPSIS_THALIANA = 3702
    BOS_TAURUS = 9913
    CAENORHABDITIS_ELEGANS = 6239
    CHLAMYDOMONAS_REINHARDTII = 3055
    DANIO_RERIO = 7955
    DICTYOSTELIUM_DISCOIDEUM = 44689
    DROSOPHILA_MELANOGASTER = 7227
    ESCHERICHIA_COLI = 562
    HEPACIVIRUS_HOMINIS = 3052230
    HOMO_SAPIENS = 9606
    MUS_MUSCULUS = 10090
    MYCOPLASMOIDES_PNEUMONIAE = 2104
    ORYZA_SATIVA = 4530
    PLASMODIUM_FALCIPARUM = 5833
    PNEUMOCYSTIS_CARINII = 4754
    RATTUS_NORVEGICUS = 10116
    SACCHAROMYCES_CEREVISIAE = 4932
    SCHIZOSACCHAROMYCES_POMBE = 4896
    TAKIFUGU_RUBRIPES = 31033
    XENOPUS_LAEVIS = 8355
    ZEA_MAYS = 4577

    @staticmethod
    def values() -> list[int]:
        return [i.value for i in Taxon]

    @classmethod
    def from_int(cls, input_value: int) -> "Taxon":
        for item in cls._member_map_.values():
            if input_value == item.value:
                return cls(item.value)
        raise ValueError(f"Unknown value '{input_value}'")

    @classmethod
    def from_string(cls, value: str) -> "Taxon":
        return from_string(value, cls)


def from_string(input_value: str, from_enum: Type[T]) -> T:
    v = input_value.lower()

    for item in from_enum:
        key = item.name.lower()
        value = str(item.value).lower()

        if v == key or v in key:
            return from_enum[item.name]
        if v == value or v in value:
            return from_enum(item.value)

    raise ValueError(f"Unknown input '{input_value}'")


async def validate_taxon_id(taxon: int | str | Taxon) -> int:
    if isinstance(taxon, Taxon):
        return taxon.value
    elif isinstance(taxon, int):
        return taxon
    elif isinstance(taxon, str):
        logger.warning(f"The provided taxon ID ('{taxon}') is a string, attempting to map it to a known integer value...")
        return Taxon.from_string(taxon).value
    else:
        raise ValueError(f"Unknown taxon type for '{taxon}': {type(taxon)}")
