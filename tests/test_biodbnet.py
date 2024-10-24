import pandas as pd
import pytest

from fast_bioservices import BioDBNet, Input, Output, Taxon


@pytest.fixture(scope="session")
def biodbnet_no_cache() -> BioDBNet:
    return BioDBNet(max_workers=1, cache=False)


@pytest.fixture(scope="session")
def biodbnet_cache() -> BioDBNet:
    return BioDBNet(max_workers=1, cache=True)


@pytest.fixture(scope="session")
def gene_ids() -> list[str]:
    return ["4318", "1376", "2576", "10089"]


@pytest.fixture(scope="session")
def gene_symbols() -> list[str]:
    return ["MMP9", "CPT2", "GAGE4", "KCNK7"]


def test_dbOrg(biodbnet_no_cache, biodbnet_cache) -> None:
    result_nocache = biodbnet_no_cache.dbOrg(
        input_db=Input.ENSEMBL_GENE_ID,
        output_db=Output.GENE_ID,
        taxon=Taxon.HOMO_SAPIENS,
    )
    result_cache = biodbnet_no_cache.dbOrg(
        input_db=Input.ENSEMBL_GENE_ID,
        output_db=Output.GENE_ID,
        taxon=Taxon.HOMO_SAPIENS,
    )

    assert isinstance(result_nocache, pd.DataFrame)
    assert isinstance(result_cache, pd.DataFrame)
    assert len(result_nocache) > 0
    assert len(result_cache) > 0


def test_getDirectOutputsForInput(biodbnet_no_cache, biodbnet_cache):
    result_nocache = biodbnet_no_cache.getDirectOutputsForInput(Input.GENE_ID)
    result_cache = biodbnet_cache.getDirectOutputsForInput(Input.GENE_ID)

    assert isinstance(result_nocache, list)
    assert isinstance(result_cache, list)
    assert len(result_nocache) > 0
    assert len(result_cache) > 0


def test_getInputs(biodbnet_no_cache, biodbnet_cache):
    result_nocache = biodbnet_no_cache.getInputs()
    result_cache = biodbnet_cache.getInputs()
    assert isinstance(result_nocache, list)
    assert isinstance(result_cache, list)
    assert len(result_nocache) > 0
    assert len(result_cache) > 0


def test_getOutputsForInput(biodbnet_no_cache, biodbnet_cache):
    result_nocache = biodbnet_no_cache.getOutputsForInput(Input.GENE_SYMBOL)
    result_cache = biodbnet_cache.getOutputsForInput(Input.GENE_SYMBOL)
    assert isinstance(result_nocache, list)
    assert isinstance(result_cache, list)
    assert len(result_nocache) > 0
    assert len(result_cache) > 0


def test_db2db(biodbnet_no_cache, biodbnet_cache, gene_ids, gene_symbols):
    result_nocache = biodbnet_no_cache.db2db(
        values=gene_ids,
        input_db=Input.GENE_ID,
        output_db=Output.GENE_SYMBOL,
        taxon=Taxon.HOMO_SAPIENS,
    )
    result_cache = biodbnet_cache.db2db(
        values=gene_ids,
        input_db=Input.GENE_ID,
        output_db=Output.GENE_SYMBOL,
        taxon=Taxon.HOMO_SAPIENS,
    )

    assert "Gene ID" in result_nocache.columns
    assert "Gene ID" in result_cache.columns
    assert "Gene Symbol" in result_nocache.columns
    assert "Gene Symbol" in result_cache.columns

    for id_, symbol in zip(gene_ids, gene_symbols):
        assert id_ in result_nocache["Gene ID"].values
        assert id_ in result_cache["Gene ID"].values
        assert symbol in result_nocache["Gene Symbol"].values
        assert symbol in result_cache["Gene Symbol"].values


def test_dbWalk(biodbnet_no_cache, biodbnet_cache):
    result_nocache = biodbnet_no_cache.dbWalk(
        values=["4318", "1376", "2576", "10089"],
        db_path=[Input.GENE_ID, Input.GENE_SYMBOL],
        taxon=Taxon.HOMO_SAPIENS,
    )
    result_cache = biodbnet_cache.dbWalk(
        values=["4318", "1376", "2576", "10089"],
        db_path=[Input.GENE_ID, Input.GENE_SYMBOL],
        taxon=Taxon.HOMO_SAPIENS,
    )

    assert len(result_nocache) == len(result_cache) == 4


@pytest.mark.skip(reason="dbReport not yet implemented")
def test_dbReport(biodbnet_no_cache):
    biodbnet_no_cache.dbReport(values=["4318"], input_db=Input.GENE_ID, taxon=Taxon.HOMO_SAPIENS)


def test_dbFind(biodbnet_no_cache, biodbnet_cache, gene_ids, gene_symbols):
    result_nocache = biodbnet_no_cache.dbFind(values=gene_ids, output_db=Output.GENE_SYNONYMS, taxon=Taxon.HOMO_SAPIENS)
    result_cache = biodbnet_cache.dbFind(values=gene_ids, output_db=Output.GENE_SYNONYMS, taxon=Taxon.HOMO_SAPIENS)

    assert len(result_nocache) == len(result_cache) == 4
    for id_, symbol in zip(gene_ids, gene_symbols):
        assert id_ in result_nocache["InputValue"].values
        assert id_ in result_cache["InputValue"].values
        assert symbol in result_nocache["Gene Symbol"].values
        assert symbol in result_cache["Gene Symbol"].values


def test_dbOrtho(biodbnet_no_cache, biodbnet_cache, gene_ids):
    result_nocache = biodbnet_no_cache.dbOrtho(
        values=gene_ids,
        input_db=Input.GENE_ID,
        output_db=Output.GENE_SYMBOL,
        input_taxon=Taxon.HOMO_SAPIENS,
        output_taxon=Taxon.MUS_MUSCULUS,
    )
    result_cache = biodbnet_cache.dbOrtho(
        values=gene_ids,
        input_db=Input.GENE_ID,
        output_db=Output.GENE_SYMBOL,
        input_taxon=Taxon.HOMO_SAPIENS,
        output_taxon=Taxon.MUS_MUSCULUS,
    )

    assert len(result_nocache) == len(result_cache) == 4

    # symbols are from Mus Musculus, not checking those
    for id_ in zip(gene_ids):
        assert id_ in result_nocache["Gene ID"].values
        assert id_ in result_cache["Gene ID"].values


@pytest.mark.skip(reason="dbAnnot tests not yet written")
def test_dbAnnot(biodbnet_no_cache):
    pass


@pytest.mark.skip(reason="getAllPathways tests not yet written")
def test_getAllPathways(biodbnet_no_cache):
    pass


@pytest.mark.skip(reason="getPathwayFromDatabase tests not yet written")
def test_getPathwayFromDatabase(biodbnet_no_cache):
    pass
