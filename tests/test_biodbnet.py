import pandas as pd
import pytest
from fast_bioservices import BioDBNet, Input, Output, Taxon


@pytest.fixture(scope="session")
def biodbnet_no_cache():
    return BioDBNet(max_workers=1, cache=False)


@pytest.fixture(scope="session")
def biodbnet_cache():
    return BioDBNet(max_workers=1, cache=True)


@pytest.fixture(scope="session")
def gene_ids():
    return ["4318", "1376", "2576", "10089"]


@pytest.fixture(scope="session")
def gene_symbols():
    return ["MMP9", "CPT2", "GAGE4", "KCNK7"]


def test_dbOrg(biodbnet_no_cache, biodbnet_cache):
    funcs = [biodbnet_no_cache.dbOrg, biodbnet_cache.dbOrg]
    for func in funcs:
        result = func(
            input_db=Input.ENSEMBL_GENE_ID,
            output_db=Output.GENE_ID,
            taxon=Taxon.HOMO_SAPIENS,
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    assert isinstance(result_nocache, pd.DataFrame)
    assert len(result_nocache) > 0

    assert isinstance(result_cache, pd.DataFrame)
    assert len(result_cache) > 0


def test_getDirectOutputsForInput(biodbnet_no_cache):
    result = biodbnet_no_cache.getDirectOutputsForInput(Input.GENE_ID)
    print(result)

    assert len(result) > 0
    assert isinstance(result, list)


def test_getInputs(biodbnet_no_cache):
    result = biodbnet_no_cache.getInputs()
    assert len(result) > 0
    assert isinstance(result, list)


def test_getOutputsForInput(biodbnet_no_cache):
    result = biodbnet_no_cache.getOutputsForInput(Input.GENE_SYMBOL)
    assert len(result) > 0
    assert isinstance(result, list)


def test_db2db(biodbnet_no_cache, gene_ids, gene_symbols):
    result = biodbnet_no_cache.db2db(
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


def test_dbWalk(biodbnet_no_cache):
    result = biodbnet_no_cache.dbWalk(
        input_values=["4318", "1376", "2576", "10089"],
        db_path=[Input.GENE_ID, Input.GENE_SYMBOL],
        taxon=Taxon.HOMO_SAPIENS,
    )

    assert len(result) == 4


@pytest.mark.skip(reason="dbReport not yet implemented")
def test_dbReport(biodbnet_no_cache):
    biodbnet_no_cache.dbReport(input_values=["4318"], input_db=Input.GENE_ID, taxon=Taxon.HOMO_SAPIENS)


def test_dbFind(biodbnet_no_cache, gene_ids, gene_symbols):
    result = biodbnet_no_cache.dbFind(input_values=gene_ids, output_db=Output.GENE_SYNONYMS, taxon=Taxon.HOMO_SAPIENS)

    assert len(result) == 4
    for id_, symbol in zip(gene_ids, gene_symbols):
        assert id_ in result["InputValue"].values
        assert symbol in result["Gene Symbol"].values


def test_dbOrtho(biodbnet_no_cache, gene_ids):
    result = biodbnet_no_cache.dbOrtho(
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
def test_dbAnnot(biodbnet_no_cache):
    pass


@pytest.mark.skip(reason="getAllPathways tests not yet written")
def test_getAllPathways(biodbnet_no_cache):
    pass


@pytest.mark.skip(reason="getPathwayFromDatabase tests not yet written")
def test_getPathwayFromDatabase(biodbnet_no_cache):
    pass
