import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from fast_bioservices.bigg import BiGG


@pytest.fixture
def bigg_instance():
    return BiGG(cache=False)


@pytest.mark.asyncio
async def test_version(bigg_instance):
    current_version = await bigg_instance.version()
    assert current_version["api_version"] == "v2"
    assert "bigg_models_version" in current_version


@pytest.mark.asyncio
async def test_models(bigg_instance):
    models = await bigg_instance.models()
    assert len(models) > 0
    assert len(models["results"]) > 0
    assert "results_count" in models


@pytest.mark.asyncio
async def test_model_details(bigg_instance):
    recon_3d = await bigg_instance.model_details("Recon3D")
    keys = [
        "metabolite_count",
        "reaction_count",
        "gene_count",
        "genome_name",
        "json_size",
        "xml_size",
        "mat_size",
        "json_gz_size",
        "xml_gz_size",
        "mat_gz_size",
        "organism",
        "genome_ref_string",
        "reference_type",
        "reference_id",
        "model_bigg_id",
        "published_filename",
    ]
    values = [
        5835,
        10600,
        2248,
        "GCF_000001405.33",
        "7.5 MB",
        "27.2 MB",
        "477.2 MB",
        "932.1 kB",
        "1.2 MB",
        "983.6 kB",
        "Homo sapiens",
        "ncbi_assembly:GCF_000001405.33",
        "pmid",
        "29457794",
        "Recon3D",
        "Recon3D.mat",
    ]

    for key, value in zip(keys, values):
        assert recon_3d[key] == value

    assert "escher_maps" in recon_3d
    assert "last_updated" in recon_3d


@pytest.mark.asyncio
async def test_json(bigg_instance):
    assert len(await bigg_instance.json("Recon3D")) > 0


@pytest.mark.asyncio
async def test_download(bigg_instance):
    ext = "xml"
    with TemporaryDirectory() as tempdir:
        as_path = Path(tempdir)
        await bigg_instance.download("Recon3D", ext=ext, download_path=as_path)
        assert f"Recon3D.{ext}" in list(os.listdir(as_path))


@pytest.mark.asyncio
async def test_model_reactions(bigg_instance):
    reactions = await bigg_instance.model_reactions("Recon3D")
    assert len(reactions) > 0
    assert "results_count" in reactions


@pytest.mark.asyncio
async def test_model_reaction_details(bigg_instance):
    reaction_details = await bigg_instance.model_reaction_details("Recon3D", "HEX1")

    general_keys = {
        "results",
        "database_links",
        "escher_maps",
        "old_identifiers",
        "bigg_id",
        "model_bigg_id",
        "count",
        "pseudoreaction",
        "name",
        "other_models_with_reaction",
        "metabolites",
    }
    results_keys = {
        "exported_reaction_id",
        "copy_number",
        "gene_reaction_rule",
        "upper_bound",
        "genes",
        "lower_bound",
        "objective_coefficient",
        "subsystem",
        "reaction_string",
    }
    database_keys = {"RHEA", "KEGG Reaction", "MetaNetX (MNX) Equation", "BioCyc", "EC Number", "SEED Reaction"}

    # Check if all elements on right are a part of the left
    assert set(reaction_details) >= general_keys
    assert set(reaction_details["results"][0].keys()) >= results_keys
    assert set(reaction_details["database_links"].keys()) >= database_keys


def test_model_metabolites(bigg_instance): ...
def test_model_metabolite_details(bigg_instance): ...
def test_model_genes(bigg_instance): ...
def test_model_gene_details(bigg_instance): ...
def test_universal_reactions(bigg_instance): ...
def test_universal_reaction_details(bigg_instance): ...
def test_universal_metabolites(bigg_instance): ...
def test_universal_metabolite_details(bigg_instance): ...
def test_search(bigg_instance): ...
