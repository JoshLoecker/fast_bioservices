from __future__ import annotations

import pandas as pd

from fast_bioservices.biothings.mygene import MyGene
from fast_bioservices.common import Taxon
from fast_bioservices.ensembl.lookup import Lookup
from fast_bioservices.ncbi.datasets import Gene


async def determine_gene_type(items: str | list[str], /) -> dict[str, str]:
    return {i: "ensembl_gene_id" if i.startswith("ENS") else "entrez_gene_id" if i.isdigit() else "gene_symbol" for i in items}


async def ensembl_to_gene_id_and_symbol(ids: str | list[str], taxon: int | str | Taxon, cache: bool = True) -> pd.DataFrame:
    data = []
    for result in await MyGene(cache=cache).gene(ids=ids, taxon=taxon):
        ensembl_data = result.get("ensembl", {})
        ensembl_gene_id = ",".join(i["gene"] for i in ensembl_data) if isinstance(ensembl_data, list) else ensembl_data.get("gene", "-")
        entrez_gene_id = result.get("entrezgene", "-")
        symbol = result.get("symbol", "-")
        data.append({"ensembl_gene_id": ensembl_gene_id, "entrez_gene_id": entrez_gene_id, "gene_symbol": symbol})
    return pd.DataFrame(data)


async def gene_id_to_ensembl_and_gene_symbol(ids: str | list[str], taxon: int | str | Taxon, cache: bool = True) -> pd.DataFrame:
    data = {"entrez_gene_id": [], "ensembl_gene_id": [], "gene_symbol": []}
    for result in await MyGene(cache=cache).gene(ids=ids, taxon=taxon):
        data["entrez_gene_id"].append(result["entrezgene"]) if "entrezgene" in result else "-"
        data["ensembl_gene_id"].append(result["ensembl"]["gene"]) if "ensembl" in result and "gene" in result["ensembl"] else "-"
        data["gene_symbol"].append(result["symbol"]) if "symbol" in result else "-"
    return pd.DataFrame(data).set_index("entrez_gene_id", drop=True)


async def gene_symbol_to_ensembl_and_gene_id(
    symbols: str | list[str], taxon: int | str | Taxon, cache: bool = True, ncbi_api_key: str = ""
) -> pd.DataFrame:
    symbols = [symbols] if isinstance(symbols, str) else symbols
    tasks = [
        Lookup(cache=cache).by_symbol(symbols=symbols, species=taxon),
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
    df = await ensembl_to_gene_id_and_symbol(ids=ids, taxon=Taxon.MUS_MUSCULUS)
    print(len(df))


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
