import io
import urllib.parse
from typing import Dict, List, Literal, Union

import pandas as pd

from fast_bioservices.base import BaseModel
from fast_bioservices.biodbnet.nodes import Input, Output, Taxon
from fast_bioservices.fast_http import FastHTTP
from fast_bioservices.log import logger


class BioDBNet(BaseModel, FastHTTP):
    _url = "https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestApi.json"

    def __init__(
        self,
        show_progress: bool = True,
        cache: bool = True,
    ):
        self._chunk_size: int = 250
        self._max_workers: int = 10

        # Initialize parent classes
        BaseModel.__init__(self, show_progress=show_progress, max_workers=self._max_workers)
        FastHTTP.__init__(self, cache=cache, max_requests_per_second=10)

    @property
    def url(self) -> str:
        return self._url

    @property
    def max_workers(self) -> int:
        return self._max_workers

    @max_workers.setter
    def max_workers(self, value: int) -> None:
        if value < 1:
            logger.debug("`max_workers` must be greater than 0, setting to 1")
            value = 1
        elif value > self._max_workers:
            logger.debug(f"`max_workers` must be less than 10 (received {value}), setting to 10")
            value = 10

        self._max_workers = value

    @property
    def show_progress(self) -> bool:
        return self._show_progress

    @show_progress.setter
    def show_progress(self, value: bool) -> None:
        self._show_progress = value

    # def _execute_with_progress(self, url: str, progress_bar: Progress, task: TaskID):
    #     result = self._get(url).json
    #     progress_bar.update(task, advance=1)
    #     return result

    # def _execute(
    #     self,
    #     urls: List[str],
    #     as_dataframe: bool = True,
    # ) -> Union[pd.DataFrame, List[dict]]:
    #     logger.debug(f"Collecting information for {len(urls)} sets of urls")
    #     if self._show_progress:
    #         with Progress(
    #             "[progress.description]{task.description}",
    #             BarColumn(),
    #             "{task.completed}/{task.total} batches",
    #             "[progress.percentage]{task.percentage:>3.0f}%",
    #             TimeRemainingColumn(),
    #         ) as progress:
    #             task = progress.add_task("[cyan]Converting...", total=len(urls))
    #             with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
    #                 partial = functools.partial(self._execute_with_progress, progress_bar=progress, task=task)
    #
    #                 results = list(executor.map(partial, urls))
    #             # Update the description
    #             progress.update(task, description="Converting... Done!")
    #     else:
    #         with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
    #             results = list(executor.map(self._get, urls))
    #             results = [r.json for r in results]
    #
    #     if as_dataframe:
    #         results: list = flatten(results)
    #         return pd.DataFrame(results)
    #     return results

    def _are_nodes_valid(
        self,
        input_: Union[Input, Output],
        output: Union[Input, Output, List[Input], List[Output]],
        direct_output: bool = False,
    ) -> bool:
        """
        The input database and output database must be different.
        :param input_: The input database.
        :type input_: Input
        :param output: The output database.
        :type output: Union[Output, list[Output]]
        :return: True if the input and output databases are different, False otherwise.
        :rtype: bool
        """

        logger.debug("Validating databases")
        if not isinstance(output, list):
            output_list = [output]
        else:
            output_list = output

        if direct_output:
            return all([o.value in self.getDirectOutputsForInput(input_) for o in output_list])
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
            taxon_url: str = f"https://www.ncbi.nlm.nih.gov/taxonomy/?term={taxon_list[i]}"
            if "No items found." in self._get(taxon_url, temp_disable_cache=True).text:
                raise ValueError(f"Unable to find taxon '{taxon_list[i]}'")
        logger.debug(f"Taxon IDs are valid: {','.join([str(i) for i in taxon_list])}")

        return taxon_list[0] if len(taxon_list) == 1 else taxon_list

    def getDirectOutputsForInput(self, input: Union[Input, Output]) -> List[str]:
        url = f"{self.url}?method=getdirectoutputsforinput&input={input.value.replace(' ', '').lower()}"
        outputs = self._get(url, temp_disable_cache=True).json
        return outputs["output"]

    def getInputs(self) -> List[str]:
        url = f"{self.url}?method=getinputs"
        inputs = self._get(url, temp_disable_cache=True).json
        return inputs["input"]

    def getOutputsForInput(self, input: Union[Input, Output]) -> List[str]:
        url = f"{self.url}?method=getoutputsforinput&input={input.value.replace(' ', '').lower()}"
        valid_outputs = self._get(url, temp_disable_cache=True).json
        return valid_outputs["output"]

    def getAllPathways(
        self,
        taxon: Union[Taxon, int],
        as_dataframe: bool = False,
    ) -> Union[pd.DataFrame, List[Dict[str, str]]]:
        taxon_id = self._validate_taxon_id(taxon)

        url = f"{self.url}?method=getpathways&pathways=1&taxonId={taxon_id}"
        result = self._get(url).json
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
        result = self._get(url).json

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
        logger.debug(f"Got {len(output_db_value.split(','))} output databases with values of: '{output_db_value}'")

        urls: list[str] = []
        for i in range(0, len(input_values), self._chunk_size):
            urls.append(self.url + "?method=db2db&format=row")
            urls[-1] += f"&input={input_db.value}"
            urls[-1] += f"&outputs={output_db_value}"
            urls[-1] += f"&inputValues={','.join(input_values[i: i + self._chunk_size])}"
            urls[-1] += f"&taxonId={taxon_id}"
            urls[-1] = urllib.parse.quote(urls[-1], safe=":/?&=")
        df = pd.DataFrame(self._execute(func=self._get, data=urls))

        df.rename(columns={"InputValue": input_db.value}, inplace=True)
        logger.debug(f"Returning dataframe with {len(df)} rows")
        return df  # type: ignore

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

        df = self._execute(urls)  # type: ignore
        df = df.rename(columns={"InputValue": str(db_path[0].value)})  # type: ignore

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
                urls[-1] += f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
                urls[-1] += f"&output={out_db.value}"
                urls[-1] += f"&taxonId={taxon_id}"

        json_result = self._execute(func=self._get, data=urls)
        master_df: pd.DataFrame = pd.DataFrame(json_result[0])
        for result in json_result[1:]:
            df = pd.DataFrame(result)  # type: ignore
            master_df = pd.merge(
                master_df,
                df,
                on=["InputValue", "Input Type"],
                how="inner",
                validate="one_to_one",
            )
        return master_df

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
                urls[-1] += f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
                urls[-1] += f"&inputTaxon={input_taxon_value}"
                urls[-1] += f"&outputTaxon={output_taxon_value}"
                urls[-1] += f"&output={out_db.value.replace(' ', '').lower()}"
                urls[-1] += "&format=row"

        json_results: List[dict] = self._execute(func=self._get, data=urls)
        master_df: pd.DataFrame = pd.DataFrame(json_results[0])
        for i, result in enumerate(json_results):
            df = pd.DataFrame(result)
            master_df = pd.merge(master_df, df, on=["InputValue"], how="inner", validate="one_to_one")

        # Remove potential duplicate columns
        for column in master_df.columns:
            if str(column).endswith("_x"):
                master_df = master_df.drop(column, axis=1)
            elif str(column).endswith("_y"):
                master_df.rename(columns={column: column[:-2]}, inplace=True)

        master_df.rename(columns={"InputValue": input_db.value}, inplace=True)

        return master_df

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

        df = pd.DataFrame(self._execute(func=self._get, data=urls))
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
        buffer = io.StringIO(self._get(url).text)
        return pd.read_csv(buffer, sep="\t", header=None, names=[input_db.value, output_db.value])


if __name__ == "__main__":
    biodbnet = BioDBNet(cache=False, show_progress=True)
    result = biodbnet.db2db(
        # input_values=["4318", "1376", "2576", "10089"],
        input_values=[str(i) for i in range(1250)],
        input_db=Input.GENE_ID,
        output_db=Output.GENE_SYMBOL,
        taxon=Taxon.HOMO_SAPIENS,
    )