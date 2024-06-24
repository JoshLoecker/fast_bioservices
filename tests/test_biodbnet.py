import pandas as pd
import pytest
from fast_bioservices import BioDBNet, Input, Output, Taxon


@pytest.fixture(scope="session")
def biodbnet_instance():
    return BioDBNet(max_workers=1, cache=False, show_progress=False)


@pytest.fixture
def gene_ids(scope="session"):
    return ["4318", "1376", "2576", "10089"]


@pytest.fixture
def gene_symbols(scope="session"):
    return ["MMP9", "CPT2", "GAGE4", "KCNK7"]


def test_dbOrg(biodbnet_instance):
    result = biodbnet_instance.dbOrg(
        input_db=Input.ENSEMBL_GENE_ID,
        output_db=Output.GENE_ID,
        taxon=Taxon.HOMO_SAPIENS,
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


def test_getDirectOutputsForInput(biodbnet_instance):
    result = biodbnet_instance.getDirectOutputsForInput(Input.GENE_ID)
    print(result)

    assert len(result) > 0
    assert isinstance(result, list)


def test_getInputs(biodbnet_instance):
    result = biodbnet_instance.getInputs()
    assert len(result) > 0
    assert isinstance(result, list)


def test_getOutputsForInput(biodbnet_instance):
    result = biodbnet_instance.getOutputsForInput(Input.GENE_SYMBOL)
    assert len(result) > 0
    assert isinstance(result, list)


def test_db2db(biodbnet_instance, gene_ids, gene_symbols):
    result = biodbnet_instance.db2db(
        input_values=gene_ids,
        input_db=Input.GENE_ID,
        output_db=Output.GENE_SYMBOL,
        taxon=Taxon.HOMO_SAPIENS,
    )

    assert "Gene ID" in result.columns
    assert "Gene Symbol" in result.columns

    for id_, symbol in zip(gene_ids, gene_symbols):
        assert id_ in result["Gene ID"].values
        assert symbol in result["Gene Symbol"].values


def test_dbWalk(biodbnet_instance):
    result = biodbnet_instance.dbWalk(
        input_values=["4318", "1376", "2576", "10089"],
        db_path=[Input.GENE_ID, Input.GENE_SYMBOL],
        taxon=Taxon.HOMO_SAPIENS,
    )

    assert len(result) == 4


@pytest.mark.skip(reason="dbReport not yet implemented")
def test_dbReport(biodbnet_instance):
    biodbnet_instance.dbReport(input_values=["4318"], input_db=Input.GENE_ID, taxon=Taxon.HOMO_SAPIENS)


def test_dbFind(biodbnet_instance, gene_ids, gene_symbols):
    result = biodbnet_instance.dbFind(
        input_values=gene_ids, output_db=Output.GENE_SYNONYMS, taxon=Taxon.HOMO_SAPIENS
    )

    assert len(result) == 4
    for id_, symbol in zip(gene_ids, gene_symbols):
        assert id_ in result["InputValue"].values
        assert symbol in result["Gene Symbol"].values


def test_dbOrtho(biodbnet_instance, gene_ids):
    result = biodbnet_instance.dbOrtho(
        input_values=gene_ids,
        input_db=Input.GENE_ID,
        output_db=Output.GENE_SYMBOL,
        input_taxon=Taxon.HOMO_SAPIENS,
        output_taxon=Taxon.MUS_MUSCULUS,
    )

    assert len(result) == 4

    # symbols are from Mus Musculus, not checking those
    for id_ in zip(gene_ids):
        assert id_ in result["Gene ID"].values


@pytest.mark.skip(reason="dbAnnot tests not yet written")
def test_dbAnnot(biodbnet_instance):
    pass


@pytest.mark.skip(reason="getAllPathways tests not yet written")
def test_getAllPathways(biodbnet_instance):
    pass


@pytest.mark.skip(reason="getPathwayFromDatabase tests not yet written")
def test_getPathwayFromDatabase(biodbnet_instance):
    pass
