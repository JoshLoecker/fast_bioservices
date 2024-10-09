import json

import pytest
from fast_bioservices.ensembl.comparative_genomics import GetHomology, HomologyResult


@pytest.fixture(scope="session")
def get_homology_instance():
    return GetHomology(cache=False, max_workers=1)


def test_get_homology_instance_creation(get_homology_instance):
    assert get_homology_instance is not None
    assert get_homology_instance._max_workers == 1


def test_get_homology_url_property(get_homology_instance):
    assert get_homology_instance.url == "https://rest.ensembl.org"


def test_by_species_with_symbol_or_id_returns_homology_results(get_homology_instance):
    results = get_homology_instance.by_species_with_symbol_or_id(
        reference_species="human",
        ensembl_id_or_symbol="ENSG00000157764",
        target_species="macaca_mulatta",
    )
    assert isinstance(results, list)
    assert len(results) > 0
    assert isinstance(results[0], HomologyResult)
    assert results[0].id == "ENSG00000157764"


def test_by_species_with_symbol_or_id_url_construction(get_homology_instance):
    results = get_homology_instance.by_species_with_symbol_or_id(
        reference_species="human",
        ensembl_id_or_symbol="ENSG00000157764",
        aligned=False,
        cigar_line=False,
        compara="vertebrates",
        external_db="test_db",
        format="full",
        sequence="protein",
        target_species="macaca_mulatta",
        target_taxon=123,
        type="orthologues",
    )
    assert results[0].id == "ENSG00000157764"
    assert results[0].method_link_type == "ENSEMBL_ORTHOLOGUES"
    assert results[0].taxonomy_level == "Catarrhini"
    assert results[0].dn_ds is None
    assert results[0].type == "ortholog_one2one"

    assert results[0].source.cigar_line == "766MD"
    assert results[0].source.id == "ENSG00000157764"
    assert results[0].source.taxon_id == 9606
    assert results[0].source.species == "homo_sapiens"
    assert results[0].source.protein_id == "ENSP00000493543"

    assert results[0].target.id == "ENSMMUG00000042793"
    assert results[0].target.cigar_line == "26M4D737M"
    assert results[0].target.species == "macaca_mulatta"
    assert results[0].target.protein_id == "ENSMMUP00000044832"
