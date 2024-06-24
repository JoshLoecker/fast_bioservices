import io
from typing import Dict, List, Literal, Union

import pandas as pd

from fast_bioservices._base import BaseModel
from fast_bioservices._fast_http import FastHTTP, Response
from fast_bioservices._log import logger
from fast_bioservices.biodbnet.nodes import Input, Output, Taxon


class BioDBNet(BaseModel, FastHTTP):
    def __init__(
        self,
        max_workers: int = 4,
        show_progress: bool = True,
        cache: bool = True,
    ):
        self._url = "https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestApi.json"
        self._chunk_size: int = 250

        BaseModel.__init__(self, url=self._url)
        FastHTTP.__init__(
            self,
            cache=cache,
            workers=max_workers,
            max_requests_per_second=10,
            show_progress=show_progress,
        )

    @property
    def url(self) -> str:
        return self._url

    def _are_nodes_valid(
        self,
        input_: Union[Input, Output],
        output: Union[Input, Output, List[Input], List[Output]],
        direct_output: bool = False,
    ) -> bool:
        """
        The input database and output database must be different.

        Parameters
        ----------
        input_ : Union[Input, Output]
            The input database
        output : Union[Input, Output, List[Input], List[Output]]
            The output database
        direct_output : bool, optional
            Get direct output node(s) for a given input node (i.e., outputs reacable by a single connection), by default False

        Returns
        -------
        bool
            True if the input and output databases are different, False otherwise.
        """

        logger.debug("Validating databases")
        output_list = [output] if not isinstance(output, list) else output

        if direct_output:
            return all(
                [o.value in self.getDirectOutputsForInput(input_) for o in output_list]
            )
        return all([o.value in self.getOutputsForInput(input_) for o in output_list])

    def _validate_taxon_id(
        self,
        taxon: Union[int, Taxon, List[Union[int, Taxon]]],
    ) -> Union[int, List[int]]:
        taxon_list: list = taxon if isinstance(taxon, list) else [taxon]
        for i in range(len(taxon_list)):
            if isinstance(taxon_list[i], Taxon):
                taxon_list[i] = taxon_list[i].value

            logger.debug(f"Validating taxon ID '{taxon_list[i]}'")
            taxon_url: str = (
                f"https://www.ncbi.nlm.nih.gov/taxonomy/?term={taxon_list[i]}"
            )
            if (
                "No items found."
                in self._get(taxon_url, temp_disable_cache=True)[0].text
            ):
                raise ValueError(f"Unable to find taxon '{taxon_list[i]}'")
        logger.debug(f"Taxon IDs are valid: {','.join([str(i) for i in taxon_list])}")

        return taxon_list[0] if len(taxon_list) == 1 else taxon_list

    def getDirectOutputsForInput(self, input: Union[Input, Output]) -> List[str]:
        url = f"{self.url}?method=getdirectoutputsforinput&input={input.value.replace(' ', '').lower()}&directOutput=1"
        print(url)
        outputs = self._get(url, temp_disable_cache=True)[0].json
        return outputs["output"]

    def getInputs(self) -> List[str]:
        url = f"{self.url}?method=getinputs"
        inputs = self._get(url, temp_disable_cache=True)[0].json
        return inputs["input"]

    def getOutputsForInput(self, input: Union[Input, Output]) -> List[str]:
        url = f"{self.url}?method=getoutputsforinput&input={input.value.replace(' ', '').lower()}"
        valid_outputs = self._get(url, temp_disable_cache=True)[0].json
        return valid_outputs["output"]

    def getAllPathways(
        self,
        taxon: Union[Taxon, int],
        as_dataframe: bool = False,
    ) -> Union[pd.DataFrame, List[Dict[str, str]]]:
        taxon_id = self._validate_taxon_id(taxon)

        url = f"{self.url}?method=getpathways&pathways=1&taxonId={taxon_id}"
        result = self._get(url)[0].json
        if as_dataframe:
            return pd.DataFrame(result)
        return result  # type: ignore

    def getPathwayFromDatabase(
        self,
        pathways: Union[
            Literal["reactome", "biocarta", "ncipid", "kegg"],
            List[Literal["reactome", "biocarta", "ncipid", "kegg"]],
        ],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
        as_dataframe: bool = True,
    ) -> Union[pd.DataFrame, List[Dict[str, str]]]:
        taxon_id = self._validate_taxon_id(taxon)

        if isinstance(pathways, str):
            pathways = [pathways]

        url = f"{self.url}?method=getpathways&pathways={','.join(pathways)}&taxonId={taxon_id}"
        result = self._get(url)[0].json

        if as_dataframe:
            return pd.DataFrame(result)
        return result  # type: ignore

    def db2db(
        self,
        input_values: List[str],
        input_db: Input,
        output_db: Union[Output, List[Output]],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        taxon_id = self._validate_taxon_id(taxon)
        if not self._are_nodes_valid(input_db, output_db):
            out_db = [output_db] if not isinstance(output_db, list) else output_db
            raise ValueError(
                "You have provided an invalid output database(s).\n"
                "A common result of this problem is including the input database as an output database.\n"
                f"Input database: {input_db.value}\n"
                f"Output database(s): {','.join([o.value for o in out_db])}"
            )
        logger.debug("Databases are valid")

        if isinstance(output_db, Output):
            output_db_value = output_db.value
        else:
            output_db_value = ",".join([o.value for o in output_db])
        logger.debug(f"Got an input database with a value of '{input_db.value}'")
        logger.debug(
            f"Got {len(output_db_value.split(','))} output databases with values of: '{output_db_value}'"
        )

        urls: list[str] = []
        for i in range(0, len(input_values), self._chunk_size):
            urls.append(self.url + "?method=db2db&format=row")
            urls[-1] += f"&input={input_db.value}"
            urls[-1] += f"&outputs={output_db_value}"
            urls[-1] += (
                f"&inputValues={','.join(input_values[i: i + self._chunk_size])}"
            )
            urls[-1] += f"&taxonId={taxon_id}"

        responses: List[Response] = self._get(urls=urls)
        df = pd.DataFrame()
        for response in responses:
            df = pd.concat([df, pd.DataFrame(response.json)])

        df.rename(columns={"InputValue": input_db.value}, inplace=True)
        logger.debug(f"Returning dataframe with {len(df)} rows")
        return df

    def dbWalk(
        self,
        input_values: List[str],
        db_path: List[Union[Input, Output]],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        taxon_id = self._validate_taxon_id(taxon)

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

        urls: list[str] = []
        for i in range(0, len(input_values), self._chunk_size):
            urls.append(self.url + "?method=dbwalk&format=row")
            urls[-1] += f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
            urls[-1] += f"&dbPath={'->'.join(databases)}"
            urls[-1] += f"&taxonId={taxon_id}"

        responses: List[Response] = self._get(urls)
        df = pd.DataFrame()
        for response in responses:
            df = pd.concat([df, pd.DataFrame(response.json)])
        df = df.rename(columns={"InputValue": str(db_path[0].value)})

        logger.debug(f"Returning dataframe with {len(df)} rows")
        return df

    def dbReport(
        self,
        input_values: List[str],
        input_db: Union[Input, Output],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ):
        taxon_id = self._validate_taxon_id(taxon)

        urls: list[str] = []
        for i in range(0, len(input_values), self._chunk_size):
            urls.append(self.url + "?method=dbreport&format=row")
            urls[-1] += f"&input={input_db.value.replace(' ', '').lower()}"
            urls[-1] += f"inputValues={','.join(input_values[i:i + self._chunk_size])}"
            urls[-1] += f"&taxonId={taxon_id}"

        return NotImplementedError

    def dbFind(
        self,
        input_values: List[str],
        output_db: Union[Output, List[Output]],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        if isinstance(output_db, Output):
            output_db = [output_db]

        taxon_id = self._validate_taxon_id(taxon)

        urls: list[str] = []
        for out_db in output_db:
            for i in range(0, len(input_values), self._chunk_size):
                urls.append(self.url + "?method=dbfind&format=row")
                urls[-1] += (
                    f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
                )
                urls[-1] += f"&output={out_db.value}"
                urls[-1] += f"&taxonId={taxon_id}"

        responses: List[Response] = self._get(urls=urls)
        df = pd.DataFrame()
        for response in responses:
            df = pd.concat([df, pd.DataFrame(response.json)])
        return df

    def dbOrtho(
        self,
        input_values: List[str],
        input_db: Input,
        output_db: Union[Output, List[Output]],
        input_taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
        output_taxon: Union[Taxon, int] = Taxon.MUS_MUSCULUS,
    ):
        input_taxon_value = self._validate_taxon_id(input_taxon)
        output_taxon_value = self._validate_taxon_id(output_taxon)

        if isinstance(output_db, Output):
            output_db = [output_db]

        urls: list[str] = []
        for out_db in output_db:
            for i in range(0, len(input_values), self._chunk_size):
                urls.append(self.url + "?method=dbortho")
                urls[-1] += f"&input={input_db.value.replace(' ', '').lower()}"
                urls[-1] += (
                    f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
                )
                urls[-1] += f"&inputTaxon={input_taxon_value}"
                urls[-1] += f"&outputTaxon={output_taxon_value}"
                urls[-1] += f"&output={out_db.value.replace(' ', '').lower()}"
                urls[-1] += "&format=row"

        responses: List[Response] = self._get(urls=urls)
        df = pd.DataFrame()
        for response in responses:
            df = pd.concat([df, pd.DataFrame(response.json)])

        # Remove potential duplicate columns
        for column in df.columns:
            if str(column).endswith("_x"):
                df = df.drop(column, axis=1)
            elif str(column).endswith("_y"):
                df.rename(columns={column: column[:-2]}, inplace=True)

        df.rename(columns={"InputValue": input_db.value}, inplace=True)

        return df

    def dbAnnot(
        self,
        input_values: List[str],
        annotations: List[
            Literal[
                "Drugs",
                "Diseases",
                "Genes",
                "GO Terms",
                "Pathways",
                "Protein Interactors",
            ]
        ],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        taxon_id = self._validate_taxon_id(taxon)

        annotations_ = [a.replace(" ", "").lower() for a in annotations]
        urls: list[str] = []
        for i in range(0, len(input_values), self._chunk_size):
            urls.append(self.url + "?method=dbannot")
            urls[-1] += f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
            urls[-1] += f"&taxonId={taxon_id}"
            urls[-1] += f"&annotations={','.join(annotations_)}"
            urls[-1] += "&format=row"

        responses: list[Response] = self._get(urls=urls)
        df = pd.DataFrame()
        for response in responses:
            df = pd.concat([df, pd.DataFrame(response.json)])
        df = df.rename(columns={"InputValue": "Input Value"})
        return df

    def dbOrg(
        self,
        input_db: Input,
        output_db: Output,
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        taxon_id = self._validate_taxon_id(taxon)

        input_db_val = input_db.value.replace(" ", "_")
        output_db_val = output_db.value.replace(" ", "_")

        url = f"https://biodbnet-abcc.ncifcrf.gov/db/dbOrgDwnld.php?file={input_db_val}__to__{output_db_val}_{taxon_id}"
        buffer = io.StringIO(self._get(url)[0].text)
        return pd.read_csv(
            buffer, sep="\t", header=None, names=[input_db.value, output_db.value]
        )


if __name__ == "__main__":
    biodbnet = BioDBNet(cache=True, show_progress=True)
    result = biodbnet.db2db(
        input_values=["4318", "1376", "2576", "10089"],
        # input_values=[str(i) for i in range(1250)],
        # annotations=["Genes"],
        input_db=Input.GENE_ID,
        output_db=Output.GENE_SYMBOL,
        taxon=Taxon.HOMO_SAPIENS,
    )
    print(result)
