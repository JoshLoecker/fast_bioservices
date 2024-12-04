from __future__ import annotations

import asyncio

import pandas as pd
import pytest

from fast_bioservices import BioDBNet, Input, Output, Taxon


@pytest.fixture
def biodbnet_no_cache() -> BioDBNet:
    return BioDBNet(cache=False)


@pytest.fixture
def biodbnet_cache() -> BioDBNet:
    return BioDBNet(cache=True)


@pytest.fixture
def gene_ids() -> list[str]:
    return ["4318", "1376", "2576", "10089"]


@pytest.fixture
def gene_symbols() -> list[str]:
    return ["MMP9", "CPT2", "GAGE4", "KCNK7"]


@pytest.mark.asyncio
async def test_db_org(biodbnet_no_cache, biodbnet_cache) -> None:
    (no_cache, with_cache) = await asyncio.gather(
        *[
            biodbnet_no_cache.db_org(
                input_db=Input.ENSEMBL_GENE_ID,
                output_db=Output.GENE_ID,
                taxon=Taxon.HOMO_SAPIENS,
            ),
            biodbnet_no_cache.db_org(
                input_db=Input.ENSEMBL_GENE_ID,
                output_db=Output.GENE_ID,
                taxon=Taxon.HOMO_SAPIENS,
            ),
        ]
    )

    assert isinstance(no_cache, pd.DataFrame)
    assert isinstance(with_cache, pd.DataFrame)
    assert len(no_cache) > 0
    assert len(with_cache) > 0


@pytest.mark.asyncio
async def test_get_direct_outputs_for_input(biodbnet_no_cache, biodbnet_cache):
    (no_cache, with_cache) = await asyncio.gather(
        *[
            biodbnet_no_cache.get_direct_outputs_for_input(Input.GENE_ID),
            biodbnet_cache.get_direct_outputs_for_input(Input.GENE_ID),
        ]
    )

    assert isinstance(no_cache, list)
    assert isinstance(with_cache, list)
    assert len(no_cache) > 0
    assert len(with_cache) > 0


@pytest.mark.asyncio
async def test_get_inputs(biodbnet_no_cache, biodbnet_cache):
    (no_cache, with_cache) = await asyncio.gather(
        *[
            biodbnet_no_cache.get_inputs(),
            biodbnet_cache.get_inputs(),
        ]
    )

    assert isinstance(no_cache, list)
    assert isinstance(with_cache, list)
    assert len(no_cache) > 0
    assert len(with_cache) > 0


@pytest.mark.asyncio
async def test_get_outputs_for_input(biodbnet_no_cache, biodbnet_cache):
    (no_cache, with_cache) = await asyncio.gather(
        *[
            biodbnet_no_cache.get_outputs_for_input(Input.GENE_SYMBOL),
            biodbnet_cache.get_outputs_for_input(Input.GENE_SYMBOL),
        ]
    )

    assert isinstance(no_cache, list)
    assert isinstance(with_cache, list)
    assert len(no_cache) > 0
    assert len(with_cache) > 0


@pytest.mark.asyncio
async def test_db2db(biodbnet_no_cache, biodbnet_cache, gene_ids, gene_symbols):
    (no_cache, with_cache) = await asyncio.gather(
        *[
            biodbnet_no_cache._db2db(
                values=gene_ids,
                input_db=Input.GENE_ID,
                output_db=Output.GENE_SYMBOL,
                taxon=Taxon.HOMO_SAPIENS,
            ),
            biodbnet_cache._db2db(
                values=gene_ids,
                input_db=Input.GENE_ID,
                output_db=Output.GENE_SYMBOL,
                taxon=Taxon.HOMO_SAPIENS,
            ),
        ]
    )

    assert "Gene ID" in no_cache.columns
    assert "Gene ID" in with_cache.columns
    assert "Gene Symbol" in no_cache.columns
    assert "Gene Symbol" in with_cache.columns

    for id_, symbol in zip(gene_ids, gene_symbols):
        assert id_ in no_cache["Gene ID"].values
        assert id_ in with_cache["Gene ID"].values
        assert symbol in no_cache["Gene Symbol"].values
        assert symbol in with_cache["Gene Symbol"].values


@pytest.mark.asyncio
async def test_db_walk(biodbnet_no_cache, biodbnet_cache):
    no_cache, with_cache = await asyncio.gather(
        *[
            biodbnet_no_cache.db_walk(
                values=["4318", "1376", "2576", "10089"],
                db_path=[Input.GENE_ID, Input.GENE_SYMBOL],
                taxon=Taxon.HOMO_SAPIENS,
            ),
            biodbnet_cache.db_walk(
                values=["4318", "1376", "2576", "10089"],
                db_path=[Input.GENE_ID, Input.GENE_SYMBOL],
                taxon=Taxon.HOMO_SAPIENS,
            ),
        ]
    )

    assert len(no_cache) == len(with_cache) == 4


@pytest.mark.skip(reason="dbReport not yet implemented")
async def test_db_report(biodbnet_no_cache):
    await biodbnet_no_cache.db_report(values=["4318"], input_db=Input.GENE_ID, taxon=Taxon.HOMO_SAPIENS)


@pytest.mark.asyncio
async def test_db_find(biodbnet_no_cache, biodbnet_cache, gene_ids, gene_symbols):
    no_cache, with_cache = await asyncio.gather(
        *[
            biodbnet_no_cache.db_find(values=gene_ids, output_db=Output.GENE_SYMBOL, taxon=Taxon.HOMO_SAPIENS),
            biodbnet_cache.db_find(values=gene_ids, output_db=Output.GENE_SYMBOL, taxon=Taxon.HOMO_SAPIENS),
        ]
    )

    assert len(no_cache) == len(with_cache) == 4
    for id_, symbol in zip(gene_ids, gene_symbols):
        assert id_ in no_cache["InputValue"].values
        assert symbol in no_cache["Gene Symbol"].values

        assert id_ in with_cache["InputValue"].values
        assert symbol in with_cache["Gene Symbol"].values


@pytest.mark.asyncio
async def test_db_ortho(biodbnet_no_cache, biodbnet_cache, gene_ids):
    no_cache, with_cache = await asyncio.gather(
        *[
            biodbnet_no_cache.db_ortho(
                values=gene_ids,
                input_db=Input.GENE_ID,
                output_db=Output.GENE_SYMBOL,
                input_taxon=Taxon.HOMO_SAPIENS,
                output_taxon=Taxon.MUS_MUSCULUS,
            ),
            biodbnet_cache.db_ortho(
                values=gene_ids,
                input_db=Input.GENE_ID,
                output_db=Output.GENE_SYMBOL,
                input_taxon=Taxon.HOMO_SAPIENS,
                output_taxon=Taxon.MUS_MUSCULUS,
            ),
        ]
    )

    assert len(no_cache) == len(with_cache) == 4

    # symbols are from Mus Musculus, not checking those
    for id_ in zip(gene_ids):
        assert id_ in no_cache["Gene ID"].values
        assert id_ in with_cache["Gene ID"].values


@pytest.mark.skip(reason="dbAnnot tests not yet written")
def test_db_annot(biodbnet_no_cache):
    pass


@pytest.mark.skip(reason="getAllPathways tests not yet written")
def test_get_all_pathways(biodbnet_no_cache):
    pass


@pytest.mark.skip(reason="getPathwayFromDatabase tests not yet written")
def test_get_pathway_from_database(biodbnet_no_cache):
    pass
