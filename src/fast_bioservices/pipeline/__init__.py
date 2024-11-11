from __future__ import annotations

import pandas as pd

from fast_bioservices.ensembl.cross_references import CrossReference
from fast_bioservices.ensembl.lookup import Lookup
from fast_bioservices.ncbi.datasets import Gene

# def determine_gene_type():
#     pass


async def ensembl_to_gene_id_and_symbol(ids: str | list[str], cache: bool = True):
    results = await CrossReference(cache=cache).by_ensembl(ids=ids, external_db_filter="EntrezGene")
    data: dict[str, list[str]] = {"ensembl_gene_id": [], "entrez_gene_id": [], "gene_symbol": []}
    for key in results:
        for result in results[key]:
            data["ensembl_gene_id"].append(key)
            data["entrez_gene_id"].append(result["primary_id"])
            data["gene_symbol"].append(result["display_id"])
    return pd.DataFrame(data).set_index("ensembl_gene_id", drop=True)


async def gene_id_to_ensembl_and_gene_symbol(ids: str | list[str], cache: bool = True, ncbi_api_key: str = "") -> pd.DataFrame:
    results = await Gene(cache=cache, api_key=ncbi_api_key).report_by_id(ids)
    length = len(results["gene"])

    data = {
        "entrez_gene_id": [results["gene"][i]["gene_id"] for i in range(length)],
        "ensembl_gene_id": [",".join(results["gene"][i]["ensembl_gene_ids"]) for i in range(length)],
        "gene_symbol": [results["gene"][i]["symbol"] for i in range(length)],
    }
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
    await ensembl_to_gene_id_and_symbol(ids=["ENSG00000157765", "ENSG00000157766"])
    # await gene_symbol_to_ensembl_and_gene_id(symbols=["HBA1", "HBA2"], species="Homo sapiens", cache=False)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
