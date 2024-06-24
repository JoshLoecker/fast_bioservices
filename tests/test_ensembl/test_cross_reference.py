import pytest
from fast_bioservices.ensembl.cross_references import CrossReference, EnsemblReference, ExternalReference


@pytest.fixture(scope="session")
def cross_reference() -> CrossReference:
    return CrossReference(max_workers=1, cache=False, show_progress=False)


def test_get_ensembl_from_external(cross_reference: CrossReference):
    expected = EnsemblReference(input="BRCA1", type="gene", id="ENSG00000012048")
    actual = cross_reference.get_ensembl_from_external(species="humans", gene_symbols="BRCA1")[0]

    assert expected.input == actual.input
    assert expected.type == actual.type
    assert expected.id == actual.id


def test_get_external_from_ensembl(cross_reference: CrossReference):
    expected = ExternalReference(
        description="Locus Reference Genomic record for BRCA1",
        info_text="",
        synonyms=[],
        dbname="ENS_LRG_gene",
        info_type="DIRECT",
        db_display_name="LRG display in Ensembl gene",
        display_id="LRG_292",
        version="0",
        primary_id="LRG_292",
    )
    actual = cross_reference.get_external_from_ensembl(ensembl_id="ENSG00000012048")[0]

    assert expected.description == actual.description
    assert expected.info_text == actual.info_text
    assert expected.synonyms == actual.synonyms
    assert expected.dbname == actual.dbname
    assert expected.info_type == actual.info_type
    assert expected.db_display_name == actual.db_display_name
    assert expected.display_id == actual.display_id
    assert expected.version == actual.version
    assert expected.primary_id == actual.primary_id
