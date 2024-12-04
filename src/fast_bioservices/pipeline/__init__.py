from __future__ import annotations

from typing import Literal

import pandas as pd
from loguru import logger

from fast_bioservices.biothings.mygene import MyGene
from fast_bioservices.common import Taxon


def _show_na_error(
    caller_name: Literal[
        "ensembl_to_gene_id_and_symbol",
        "gene_id_to_ensembl_and_gene_symbol",
        "gene_symbol_to_ensembl_and_gene_id",
    ],
) -> None:
    data_type = {
        "ensembl_to_gene_id_and_symbol": "Gene ID and Gene Symbol",
        "gene_id_to_ensembl_and_gene_symbol": "Ensembl ID and Gene Symbol",
        "gene_symbol_to_ensembl_and_gene_id": "Ensembl ID and Gene ID",
    }.get(caller_name, None)
    if data_type is None:
        raise ValueError("Invalid caller_name")
    logger.critical(f"All {data_type} values are NA. Did you use the correct Taxon ID? Rerunning without cache.")


async def determine_gene_type(items: str | list[str], /) -> dict[str, str]:
    return {
        i: "ensembl_gene_id"
        if i.startswith("ENS") and i[-1].isdigit()
        else "entrez_gene_id"
        if i.isdigit()
        else "gene_symbol"
        for i in items
    }


async def ensembl_to_gene_id_and_symbol(
    ids: str | list[str],
    taxon: int | str | Taxon,
    cache: bool = True,
    rerun_if_na: bool = True,
) -> pd.DataFrame:
    data = []
    for result in await MyGene(cache=cache).gene(ids=ids, taxon=taxon):
        ensembl_data = result.get("ensembl", {})
        ensembl_gene_id = (
            ",".join(i["gene"] for i in ensembl_data)
            if isinstance(ensembl_data, list)
            else ensembl_data.get("gene", "-")
        )
        entrez_gene_id = result.get("entrezgene", "-")
        symbol = result.get("symbol", "-")
        data.append({"ensembl_gene_id": ensembl_gene_id, "entrez_gene_id": entrez_gene_id, "gene_symbol": symbol})

    # if all gene id and gene symbol are nan, re-run without cache
    df = pd.DataFrame(data)
    if rerun_if_na and df["entrez_gene_id"].isna().all() and df["gene_symbol"].isna().all():
        _show_na_error("ensembl_to_gene_id_and_symbol")
        return await ensembl_to_gene_id_and_symbol(ids, taxon, cache=False)

    return df


async def gene_id_to_ensembl_and_gene_symbol(
    ids: str | list[str], taxon: int | str | Taxon, cache: bool = True, rerun_if_na: bool = True
) -> pd.DataFrame:
    data = {"entrez_gene_id": [], "ensembl_gene_id": [], "gene_symbol": []}
    for result in await MyGene(cache=cache).gene(ids=ids, taxon=taxon):
        data["entrez_gene_id"].append(result["entrezgene"]) if "entrezgene" in result else "-"
        data["ensembl_gene_id"].append(result["ensembl"]["gene"]) if "ensembl" in result and "gene" in result[
            "ensembl"
        ] else "-"
        data["gene_symbol"].append(result["symbol"]) if "symbol" in result else "-"

    df = pd.DataFrame(data).set_index("entrez_gene_id", drop=True)
    if rerun_if_na and df["ensembl_gene_id"].isna().all() and df["gene_symbol"].isna().all():
        _show_na_error("gene_id_to_ensembl_and_gene_symbol")
        return await gene_id_to_ensembl_and_gene_symbol(ids, taxon, cache=False)

    return pd.DataFrame(data).set_index("entrez_gene_id", drop=True)


async def gene_symbol_to_ensembl_and_gene_id(
    symbols: str | list[str],
    taxon: int | str | Taxon,
    cache: bool = True,
    rerun_if_na: bool = True,
) -> pd.DataFrame:
    symbols = [symbols] if isinstance(symbols, str) else symbols
    data: dict[str, list[str | pd.NA]] = {"gene_symbol": [], "ensembl_gene_id": [], "entrez_gene_id": []}
    for response in await MyGene(cache=cache).query(items=symbols, taxon=taxon, scopes="symbol"):
        data["gene_symbol"].append(response["query"])

        if "notfound" in response:
            data["ensembl_gene_id"].append(pd.NA)
            data["entrez_gene_id"].append(pd.NA)
            continue

        data["ensembl_gene_id"].append(response.get("ensembl.gene", pd.NA))
        data["entrez_gene_id"].append(response.get("entrezgene", pd.NA))

    df = pd.DataFrame(data)
    if rerun_if_na and df["ensembl_gene_id"].isna().all() and df["entrez_gene_id"].isna().all():
        _show_na_error("gene_symbol_to_ensembl_and_gene_id")
        return await gene_symbol_to_ensembl_and_gene_id(symbols, taxon, cache=False)

    # combine duplicates of the gene_symbol column
    df = df.groupby("gene_symbol").agg(
        ensembl_gene_id=("ensembl_gene_id", lambda x: x.dropna().tolist()),
        entrez_gene_id=("entrez_gene_id", lambda x: x.dropna().tolist()),
    )

    # remove lists in ensembl_gene_id and entrez_gene_id that are created as a result of the aggregate function
    # additionally, some items are double nested (`[[]]`); the first list is removed on the apply, then the second is removed in the applymap
    df["ensembl_gene_id"] = df["ensembl_gene_id"].apply(lambda x: pd.NA if len(x) == 0 else x[0])
    df["entrez_gene_id"] = df["entrez_gene_id"].apply(lambda x: pd.NA if len(x) == 0 else x[0])
    df = df.map(lambda x: x[0] if isinstance(x, list) else x)

    return df


async def _main():
    # df = pd.read_csv("/Users/joshl/Projects/AcuteRadiationSickness/data/captopril/gene_counts/gene_counts_matrix_full_waterIrradiated24hr.csv")
    # ids = df["genes"].tolist()
    df = await gene_symbol_to_ensembl_and_gene_id(
        symbols=[
            "MIR1302-2HG",
            "FAM138A",
            "OR4F5",
            "AL627309.1",
            "AL627309.3",
            "AL627309.2",
            "AL627309.5",
            "AL627309.4",
            "AP006222.2",
            "AL732372.1",
        ],
        # symbols=["MIR1302-2HG", "FAM138A", "OR4F5", "OR4F29", "OR4F16", "LINC01409", "FAM87B", "LINC01128", "LINC00115", "FAM41C"],
        taxon=Taxon.HOMO_SAPIENS,
        cache=False,
    )
    print(df)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
