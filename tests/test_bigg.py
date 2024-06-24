import os

import pytest
from fast_bioservices import BiGG


@pytest.fixture(scope="session")
def bigg_instance():
    return BiGG(max_workers=1, cache=False, show_progress=False)


def test_version(bigg_instance):
    current_version = bigg_instance.version()
    assert current_version["api_version"] == "v2"
    assert "bigg_models_version" in current_version.keys()


def test_models(bigg_instance):
    models = bigg_instance.models()
    assert len(models.keys()) > 0
    assert len(models["results"]) > 0
    assert "results_count" in models.keys()


def test_model_details(bigg_instance):
    recon_3d = bigg_instance.model_details("Recon3D")
    keys = ["metabolite_count", "reaction_count", "gene_count", "genome_name", "json_size", "xml_size", "mat_size", "json_gz_size", "xml_gz_size", "mat_gz_size", "organism", "genome_ref_string", "reference_type", "reference_id", "model_bigg_id", "published_filename"]  # fmt: skip
    values = [5835, 10600, 2248, "GCF_000001405.33", "7.5 MB", "27.2 MB", "477.2 MB", "932.1 kB", "1.2 MB", "983.6 kB", "Homo sapiens", "ncbi_assembly:GCF_000001405.33", "pmid", "29457794", "Recon3D", "Recon3D.mat"]  # fmt: skip

    for key, value in zip(keys, values):
        assert recon_3d[key] == value

    assert "escher_maps" in recon_3d.keys()
    assert "last_updated" in recon_3d.keys()


def test_json(bigg_instance):
    assert len(bigg_instance.json("Recon3D").keys()) > 0


def test_download(bigg_instance):
    download_path = os.getcwd()
    bigg_instance.download("Recon3D", format="json.gz", download_path=download_path)
    assert "Recon3D.json.gz" in list(os.listdir())
    os.unlink(f"{download_path}/Recon3D.json.gz")


def test_model_reactions(bigg_instance):
    reactions = bigg_instance.model_reactions("Recon3D")
    assert len(reactions.keys()) > 0
    assert "results_count" in reactions.keys()


def test_model_reaction_details(bigg_instance):
    reaction_details = bigg_instance.model_reaction_details("Recon3D", "HEX1")

    general_keys = {"results", "database_links", "escher_maps", "old_identifiers", "bigg_id", "model_bigg_id", "count", "pseudoreaction", "name", "other_models_with_reaction", "metabolites"}  # fmt: skip
    results_keys = {"exported_reaction_id", "copy_number", "gene_reaction_rule", "upper_bound", "genes", "lower_bound", "objective_coefficient", "subsystem", "reaction_string"}  # fmt: skip
    database_keys = {"RHEA", "KEGG Reaction", "MetaNetX (MNX) Equation", "BioCyc", "EC Number", "SEED Reaction"}  # fmt: skip

    # Check if all elements on right are a part of the left
    assert set(reaction_details.keys()) >= general_keys
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
