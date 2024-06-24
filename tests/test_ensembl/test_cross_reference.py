import pytest
from fast_bioservices.ensembl.cross_references import CrossReference, ExternalReference


@pytest.fixture(scope="session")
def cross_reference() -> CrossReference:
    return CrossReference(max_workers=1)


def test_get_ensembl_from_external(cross_reference: CrossReference):
    response = cross_reference.get_ensembl_from_external(species="humans", gene_symbols=["BRCA1", "BRCA2"])
    print(response)
    assert 1 == 2
