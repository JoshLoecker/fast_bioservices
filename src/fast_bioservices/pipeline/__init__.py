from __future__ import annotations

import pandas as pd

from fast_bioservices.biothings.mygene import MyGene
from fast_bioservices.ensembl.cross_references import CrossReference
from fast_bioservices.ensembl.lookup import Lookup
from fast_bioservices.ncbi.datasets import Gene


async def determine_gene_type(items: str | list[str], species: str, api_key: str = ""):
    results: dict[str, str] = {}

    for i in items:
        if i.startswith("ENS"):
            results[i] = "ensembl_gene_id"
        elif i.isdigit():
            results[i] = "entrez_gene_id"
        else:
            results[i] = "gene_symbol"

    reference = CrossReference(cache=False)
    ncbi_gene = Gene(cache=False, api_key=api_key)
    test_ensembl = await reference.by_ensembl(ids=items)
    test_ncbi = await ncbi_gene.report_by_id([i for i in items if i.isdigit()])

    print(test_ncbi)

    for i in items:
        if "error" not in test_ensembl[i]:  # Item is an ensembl gene id
            results[i] = "ensembl_gene_id"
        # if test_ensembl[i]["error"] == f"ID '{i}' not found":
        # if test_ensembl[i]["error"] == f'ID "{i}" not found':

    # print(ensembl_results)
    # print(external_results)


async def ensembl_to_gene_id_and_symbol(ids: str | list[str], cache: bool = True) -> pd.DataFrame:
    data = {"ensembl_gene_id": [], "entrez_gene_id": [], "gene_symbol": []}
    for result in await MyGene(cache=cache).gene(ids=ids):
        data["ensembl_gene_id"].append(result["ensembl"]["gene"]) if "ensembl" in result and "gene" in result["ensembl"] else "-"
        data["entrez_gene_id"].append(result["entrezgene"]) if "entrezgene" in result else "-"
        data["gene_symbol"].append(result["symbol"]) if "symbol" in result else "-"
    return pd.DataFrame(data).set_index("ensembl_gene_id", drop=True)


async def gene_id_to_ensembl_and_gene_symbol(ids: str | list[str], cache: bool = True) -> pd.DataFrame:
    data = {"entrez_gene_id": [], "ensembl_gene_id": [], "gene_symbol": []}
    for result in await MyGene(cache=cache).gene(ids=ids):
        data["entrez_gene_id"].append(result["entrezgene"]) if "entrezgene" in result else "-"
        data["ensembl_gene_id"].append(result["ensembl"]["gene"]) if "ensembl" in result and "gene" in result["ensembl"] else "-"
        data["gene_symbol"].append(result["symbol"]) if "symbol" in result else "-"
    return pd.DataFrame(data).set_index("entrez_gene_id", drop=True)


async def gene_symbol_to_ensembl_and_gene_id(symbols: str | list[str], species: str, cache: bool = True, ncbi_api_key: str = "") -> pd.DataFrame:
    symbols = [symbols] if isinstance(symbols, str) else symbols
    tasks = [
        Lookup(cache=cache).by_symbol(symbols=symbols, species=species),
        Gene(cache=cache, api_key=ncbi_api_key).report_by_symbol(symbols=symbols, taxon=species),
    ]
    ensembl_response, ncbi_response = await asyncio.gather(*tasks)

    data: dict[str, list[str]] = {
        "gene_symbol": symbols,
        "ensembl_gene_id": [response["id"] for response in ensembl_response],
        "entrez_gene_id": [response["gene_id"] for response in ncbi_response["gene"]],
    }
    df = pd.DataFrame(data).set_index("gene_symbol", drop=True)
    return df


async def _main():
    # await determine_gene_type(items=["ENSG00000170558", "1000", "CDH2"], species="human")
    #         "--matrix", "/Users/joshl/Projects/AcuteRadiationSickness/data/captopril/gene_counts/gene_counts_matrix_full_waterIrradiated24hr.csv"
    df = pd.read_csv("/Users/joshl/Projects/AcuteRadiationSickness/data/captopril/gene_counts/gene_counts_matrix_full_waterIrradiated24hr.csv")
    ids = df["genes"].tolist()
    ids = ids[:20]
    await ensembl_to_gene_id_and_symbol(ids=ids)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
