from __future__ import annotations

import asyncio
import io
import json
from typing import Literal

import pandas as pd
from loguru import logger

from fast_bioservices.biodbnet.nodes import Input, Output
from fast_bioservices.common import Taxon, validate_taxon_id
from fast_bioservices.fast_http import _AsyncHTTPClient


class BioDBNet(_AsyncHTTPClient):
    def __init__(self, cache: bool = True, chunk_size: int = 250):
        """Connect to BioDBNet."""
        super().__init__(cache=cache, max_requests_per_second=10)
        self._url = "https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestApi.json"
        self._cache: bool = cache
        self._chunk_size: int = chunk_size

    @property
    def url(self) -> str:
        """Return the root URL."""
        return self._url

    async def _are_nodes_valid(
        self, value: Input | Output, to: Input | Output | list[Input | Output], direct_output: bool = False
    ) -> bool:
        """Determine if the input database and output database are different.

        :param value: Input | Output: The input database
        :param to: Input | Output | list[Input | Output]: The output database
        :param direct_output: bool, optional: Get direct output node(s) for a given input node
            (i.e., outputs reacable by a single connection), by default False
        :return: bool: True if the input and output databases are different, False otherwise.
        """
        logger.debug("Validating databases")
        output_list = to if isinstance(to, list) else [to]

        if direct_output:
            return all([o.value in await self.get_direct_outputs_for_input(value) for o in output_list])
        return all([o.value in await self.get_outputs_for_input(value) for o in output_list])

    async def get_direct_outputs_for_input(self, value: Input | Output) -> list[str]:
        """Get direct outputs for a given input."""
        url = f"{self.url}?method=getdirectoutputsforinput&input={value.value.replace(' ', '').lower()}&directOutput=1"
        outputs = (await self._get(url, temp_disable_cache=True, log_on_complete=False))[0]
        as_json = json.loads(outputs)
        return as_json["output"]

    async def get_inputs(self) -> list[str]:
        """Get all possible inputs."""
        url = f"{self.url}?method=getinputs"
        inputs = (await self._get(url, temp_disable_cache=True, log_on_complete=False))[0]
        as_json = json.loads(inputs)
        return as_json["input"]

    async def get_outputs_for_input(self, value: Input | Output) -> list[str]:
        """Get a list of outputs for a given input."""
        url = f"{self.url}?method=getoutputsforinput&input={value.value.replace(' ', '').lower()}"
        response = (await self._get(url, temp_disable_cache=True, log_on_complete=False))[0].decode()
        valid_outputs = json.loads(response)
        return valid_outputs["output"]

    async def get_all_pathways(
        self,
        taxon: Taxon | int,
        as_dataframe: bool = False,
    ) -> pd.DataFrame | list[dict[str, str]]:
        """Get all pathways."""
        taxon_id = await validate_taxon_id(taxon)

        url = f"{self.url}?method=getpathways&pathways=1&taxonId={taxon_id}"
        response = (await self._get(url))[0].decode()
        as_json = json.loads(response)
        return pd.DataFrame(as_json) if as_dataframe else as_json

    async def get_pathway_from_database(
        self,
        pathways: Literal["reactome", "biocarta", "ncipid", "kegg"]
        | list[Literal["reactome", "biocarta", "ncipid", "kegg"]],
        taxon: Taxon | int = Taxon.HOMO_SAPIENS,
        as_dataframe: bool = True,
    ) -> pd.DataFrame | list[dict[str, str]]:
        """Get pathways from a specific database."""
        taxon_id = await validate_taxon_id(taxon)

        if isinstance(pathways, str):
            pathways = [pathways]

        url = f"{self.url}?method=getpathways&pathways={','.join(sorted(pathways))}&taxonId={taxon_id}"
        response = (await self._get(url))[0].decode()
        as_json = json.loads(response)
        return pd.DataFrame(as_json) if as_dataframe else as_json

    async def async_db2db(
        self,
        values: list[str],
        input_db: Input,
        output_db: Output | list[Output],
        taxon: Taxon | int = Taxon.HOMO_SAPIENS,
    ):
        """Async conversion from one database to another."""
        return await self._db2db(values=values, input_db=input_db, output_db=output_db, taxon=taxon)

    def db2db(
        self,
        values: list[str],
        input_db: Input,
        output_db: Output | list[Output],
        taxon: Taxon | int = Taxon.HOMO_SAPIENS,
    ):
        """Sync conversion from one database to another."""
        return asyncio.run(self._db2db(values=values, input_db=input_db, output_db=output_db, taxon=taxon))

    async def _db2db(
        self,
        values: list[str],
        input_db: Input,
        output_db: Output | list[Output],
        taxon: Taxon | int = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        taxon_id = await validate_taxon_id(taxon)

        if not await self._are_nodes_valid(input_db, output_db):
            out_db: list = output_db if isinstance(output_db, list) else [output_db]
            raise ValueError(
                "You have provided an invalid output database(s).\n"
                "A common result of this problem is including the input database as an output database.\n"
                f"Input database: {input_db.value}\n"
                f"Output database(s): {','.join([o.value for o in out_db])}"
            )
        logger.debug("Databases are valid")

        if isinstance(output_db, Output):
            output_db_value = output_db.value.lower().replace(" ", "")
        else:
            output_db_value = ",".join(sorted([o.value.lower().replace(" ", "") for o in output_db]))
        logger.debug(f"Got an input database with a value of '{input_db.value.lower().replace(' ', '')}'")
        logger.debug(f"Got {len(output_db_value.split(','))} output databases with values of: '{output_db_value}'")

        values.sort()
        urls: list[str] = [
            (
                f"{self.url}?"
                f"method=db2db&"
                f"format=row&"
                f"input={input_db.value.lower().replace(' ', '')}&"
                f"outputs={output_db_value}&"
                f"inputValues={','.join(values[i:i + self._chunk_size])}&"
                f"taxonId={taxon_id}"
            )
            for i in range(0, len(values), self._chunk_size)
        ]
        responses: list[str] = [
            item
            for response in await self._get(urls=urls, extensions={"force_cache": True})
            for item in json.loads(response.decode())
        ]
        df = pd.DataFrame(responses).rename(columns={"InputValue": input_db.value})
        logger.debug(f"Returning dataframe with {len(df)} rows")
        return df

    async def db_walk(
        self,
        values: list[str],
        db_path: list[Input | Output],
        taxon: Taxon | int = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        """Determine the edges to go from one database to another."""
        taxon_id = await validate_taxon_id(taxon)

        for i in range(len(db_path) - 1):
            current_db = db_path[i]
            next_db = db_path[i + 1]

            if not self._are_nodes_valid(current_db, next_db, direct_output=True):
                raise ValueError(
                    "You have provided an invalid output database.\n"
                    f"Unable to navigate from '{current_db.value}' to '{next_db.value}'"
                )
        logger.debug("Databases are valid")
        databases: list[str] = [d.value.replace(" ", "").lower() for d in db_path]

        values.sort()
        databases.sort()
        urls: list[str] = []
        for i in range(0, len(values), self._chunk_size):
            urls.append(  # noqa: PERF401, do not require list comprehensions
                f"{self.url}?method=dbwalk&"
                f"format=row&"
                f"inputValues={','.join(values[i:i + self._chunk_size])}&"
                f"dbPath={'->'.join(databases)}&"
                f"taxonId={taxon_id}"
            )

        responses: list[bytes] = [item for response in await self._get(urls) for item in json.loads(response)]
        df = pd.DataFrame(responses).rename(columns={"InputValue": str(db_path[0].value)})
        logger.debug(f"Returning dataframe with {len(df)} rows")
        return df

    async def db_report(self, values: list[str], input_db: Input | Output, taxon: Taxon | int = Taxon.HOMO_SAPIENS):
        """Report all database identifiers and annotations related to the input."""
        taxon_id = await validate_taxon_id(taxon)
        urls: list[str] = []
        for i in range(0, len(values), self._chunk_size):
            urls.append(  # noqa: PERF401, do not require list comprehensions
                f"{self.url}?method=dbreport&"
                f"format=row&"
                f"input={input_db.value.replace(' ', '').lower()}&"
                f"inputValues={','.join(values[i:i + self._chunk_size])}&"
                f"taxonId={taxon_id}"
            )
        return NotImplementedError

    async def db_find(
        self,
        values: list[str],
        output_db: Output | list[Output],
        taxon: Taxon | int = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        """Determine the database of input values."""
        taxon_id = await validate_taxon_id(taxon)
        values = sorted(values)
        urls: list[str] = []
        output_db: list[Output] = [output_db] if isinstance(output_db, Output) else output_db

        for out_db in output_db:
            for i in range(0, len(values), self._chunk_size):
                urls.append(  # noqa: PERF401, do not require list comprehensions
                    f"{self.url}?method=dbfind&"
                    f"format=row&"
                    f"inputValues={','.join(values[i:i + self._chunk_size])}&"
                    f"output={out_db.value.lower().replace(' ', '')}&taxonId={taxon_id}"
                )
        all_responses = []
        for response in await self._get(urls=urls):
            all_responses.extend(json.loads(response.decode()))
        df = pd.DataFrame(all_responses).groupby("InputValue", as_index=False).first()
        return df

    async def db_ortho(
        self,
        values: list[str],
        input_db: Input,
        output_db: Output | list[Output],
        input_taxon: Taxon | int = Taxon.HOMO_SAPIENS,
        output_taxon: Taxon | int = Taxon.MUS_MUSCULUS,
    ):
        """Run ortholog conversions for the given input."""
        input_taxon_value, output_taxon_value = await asyncio.gather(
            *[validate_taxon_id(input_taxon), validate_taxon_id(output_taxon)]
        )

        if isinstance(output_db, Output):
            output_db = [output_db]

        output_db.sort()
        values.sort()
        urls: list[str] = []
        for out_db in output_db:
            for i in range(0, len(values), self._chunk_size):
                urls.append(  # noqa: PERF401, do not require list comprehensions
                    f"{self.url}?method=dbortho&"
                    f"input={input_db.value.replace(' ', '').lower()}&"
                    f"inputValues={','.join(values[i:i + self._chunk_size])}&"
                    f"inputTaxon={input_taxon_value}&"
                    f"outputTaxon={output_taxon_value}&"
                    f"output={out_db.value.replace(' ', '').lower()}&"
                    f"format=row"
                )

        responses: list[bytes] = [item for response in await self._get(urls) for item in json.loads(response)]
        df = pd.DataFrame(responses).rename(columns={"InputValue": input_db.value})

        # Remove potential duplicate columns
        for column in df.columns:
            if str(column).endswith("_x"):
                df = df.drop(column, axis=1)
            elif str(column).endswith("_y"):
                df.rename(columns={column: column[:-2]}, inplace=True)

        return df

    async def db_annot(
        self,
        values: list[str],
        annotation: list[
            Literal[
                "Drugs",
                "Diseases",
                "Genes",
                "GO Terms",
                "Pathways",
                "Protein Interactors",
            ]
        ],
        taxon: Taxon | int = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        """Annotate biological identifiers."""
        taxon_id = await validate_taxon_id(taxon)
        annotation = [a.replace(" ", "").lower() for a in sorted(annotation)]

        values.sort()
        urls: list[str] = []
        for i in range(0, len(values), self._chunk_size):
            urls.append(  # noqa: PERF401, do not require list comprehensions
                f"{self.url}?method=dbannot&"
                f"inputValues={','.join(values[i:i + self._chunk_size])}&"
                f"taxonId={taxon_id}&"
                f"annotations={','.join(annotation)}&"
                f"format=row"
            )

        responses: list[bytes] = await self._get(urls=urls)
        return pd.DataFrame(responses)

    async def db_org(self, input_db: Input, output_db: Output, taxon: Taxon | int = Taxon.HOMO_SAPIENS) -> pd.DataFrame:
        """Organism-wide conversions."""
        taxon_id = await validate_taxon_id(taxon)
        input_db_val = input_db.value.replace(" ", "_")
        output_db_val = output_db.value.replace(" ", "_")

        url = f"https://biodbnet-abcc.ncifcrf.gov/db/dbOrgDwnld.php?file={input_db_val}__to__{output_db_val}_{taxon_id}"
        response = await self._get(url)
        buffer = io.StringIO(response[0].decode())
        return pd.read_csv(buffer, sep="\t", header=None, names=[input_db.value, output_db.value])
