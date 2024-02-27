import concurrent.futures
import io
import os
from typing import List, Literal, Union

import modguard
import pandas as pd
import tqdm.contrib.concurrent

from fast_bioservices.fast_http import HTTP
from fast_bioservices.log import logger
from fast_bioservices.nodes import Input, Output, Taxon
from fast_bioservices.utils import flatten


class BioDBNet:
    _url = "https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestApi.json"
    
    def __init__(
        self,
        max_workers: int = min(32, os.cpu_count() + 4),
        show_progress: bool = True,
        cache: bool = True,
    ):
        self._chunk_size: int = 100
        self._worker_limit: int = 32
        self._max_workers: int = max_workers
        self._http: HTTP = HTTP(cache=cache)
        self._show_progress: bool = show_progress
    
    @modguard.public
    @property
    def max_workers(self) -> int:
        return self._max_workers
    
    @modguard.public
    @max_workers.setter
    def max_workers(self, value: int) -> None:
        if value < 1:
            logger.debug("`max_workers` must be greater than 0, setting to 1")
            value = 1
        elif value > self._worker_limit:
            logger.debug(
                f"`max_workers` must be less than 32 (received {value}), setting to 32"
            )
            value = os.cpu_count() + 4
        
        self._max_workers = value
    
    @modguard.public
    @property
    def show_progress(self) -> bool:
        return self._show_progress
    
    @modguard.public
    @show_progress.setter
    def show_progress(self, value: bool) -> None:
        self._show_progress = value
    
    def _execute(
        self, urls: List[str], as_dataframe: bool = True
    ) -> Union[pd.DataFrame, List[dict]]:
        logger.debug(f"Collecting information for {len(urls)} sets of urls")
        
        self._http.warned = False
        if self._show_progress:
            results = tqdm.contrib.concurrent.thread_map(
                self._http.get_json, urls, max_workers=self._max_workers, position=99
            )
        else:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self._max_workers
            ) as executor:
                results = list(executor.map(self._http.get_json, urls))
        
        if as_dataframe:
            results = flatten(results)
            return pd.DataFrame(results)
        return results
    
    def _are_nodes_valid(
        self,
        input_: Union[Input, Output],
        output: Union[Union[Input, Output], List[Union[Input, Output]]],
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
            output = [output]
        
        if direct_output:
            return all([o.value in self.getDirectOutputsForInput(input_) for o in output])
        return all([o.value in self.getOutputsForInput(input_) for o in output])
    
    def _validate_taxon_id(self, taxon: Union[int, List[int], Taxon, List[Taxon]]) -> Union[int, List[int]]:
        taxon_list: list[int] = []
        if isinstance(taxon, Taxon):
            taxon_list.append(taxon.value)
        elif isinstance(taxon, List):
            if isinstance(taxon[0], Taxon):
                taxon_list.extend([t.value for t in taxon])
            else:
                taxon_list.extend([t for t in taxon])
        
        for t in taxon_list:
            logger.debug(f"Validating taxon ID '{t}'")
            taxon_url: str = f"https://www.ncbi.nlm.nih.gov/taxonomy/?term={t}"
            if "No items found." in self._http._get_internal_text(taxon_url):
                raise ValueError(f"Unable to find taxon '{t}'")
        logger.debug(f"Taxon IDs are valid: {','.join([str(i) for i in taxon_list])}")
        return taxon_list[0] if len(taxon_list) == 1 else taxon_list
    
    @modguard.public
    def getDirectOutputsForInput(self, input: Union[Input, Output]) -> List[str]:
        url = f"{self._url}?method=getdirectoutputsforinput&input={input.value.replace(' ', '').lower()}"
        outputs = self._http._get_internal_json(url)["output"]
        return outputs
    
    @modguard.public
    def getInputs(self) -> List[str]:
        url = f"{self._url}?method=getinputs"
        inputs = self._http._get_internal_json(url)["input"]
        return inputs
    
    @modguard.public
    def getOutputsForInput(self, input: Input) -> List[str]:
        url = f"{self._url}?method=getoutputsforinput&input={input.value.replace(' ', '').lower()}"
        valid_outputs: list[str] = self._http._get_internal_json(url)["output"]
        return valid_outputs
    
    @modguard.public
    def getAllPathways(
        self,
        taxon: Union[Taxon, int],
        as_dataframe: bool = False
    ) -> Union[pd.DataFrame, List[dict[str, str]]]:
        taxon = self._validate_taxon_id(taxon)
        
        url = f"{self._url}?method=getpathways&pathways=1&taxonId=9606"
        result = self._http.get_json(url)
        if as_dataframe:
            return pd.DataFrame(result)
        return result
    
    @modguard.public
    def getPathwayFromDatabase(
        self,
        pathways: Union[
            Literal["reactome", "biocarta", "ncipid", "kegg"],
            List[Literal["reactome", "biocarta", "ncipid", "kegg"]]
        ],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
        as_dataframe: bool = True
    ) -> Union[pd.DataFrame, List[dict[str, str]]]:
        taxon = self._validate_taxon_id(taxon)
        
        if isinstance(pathways, str):
            pathways = [pathways]
        
        url = f"{self._url}?method=getpathways&pathways={','.join(pathways)}&taxonId={taxon}"
        result = self._http.get_json(url)
        
        if as_dataframe:
            return pd.DataFrame(result)
        return result
    
    @modguard.public
    def db2db(
        self,
        input_values: List[str],
        input_db: Input,
        output_db: Union[Output, list[Output]],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        taxon = self._validate_taxon_id(taxon)
        
        if not self._are_nodes_valid(input_db, output_db):
            out_db = [output_db] if isinstance(output_db, list) else output_db
            raise ValueError(
                "You have provided an invalid output database(s).\n"
                "A common result of this problem is including the input database as an output database.\n"
                f"Input database: {input_db.value}\n"
                f"Output database(s): {','.join([o.value for o in out_db])}"
            )
        logger.debug("Databases are valid")
        
        input_db = input_db.value
        if isinstance(output_db, Output):
            output_db = [output_db]
        output_db = ",".join([o.value for o in output_db])
        logger.debug(f"Got an input database with a value of '{input_db}'")
        logger.debug(
            f"Got {len(output_db.split(','))} output databases with values of: {output_db}"
        )
        
        urls: list[str] = []
        for i in range(0, len(input_values), self._chunk_size):
            urls.append(self._url + "?method=db2db&format=row")
            urls[-1] += f"&input={input_db}"
            urls[-1] += f"&outputs={output_db}"
            urls[-1] += f"&inputValues={','.join(input_values[i: i + self._chunk_size])}"
            urls[-1] += f"&taxonId={taxon}"
        print(urls)
        df = self._execute(urls)
        df.rename(columns={"InputValue": input_db}, inplace=True)
        logger.debug(f"Returning dataframe with {len(df)} rows")
        return df
    
    @modguard.public
    def dbWalk(
        self,
        input_values: List[str],
        db_path: List[Union[Input, Output]],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        
        taxon = self._validate_taxon_id(taxon)
        
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
            urls.append(self._url + "?method=dbwalk&format=row")
            urls[-1] += f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
            urls[-1] += f"&dbPath={'->'.join(databases)}"
            urls[-1] += f"&taxonId={taxon}"
        
        df: pd.DataFrame = self._execute(urls)
        df = df.rename(columns={"InputValue": str(db_path[0].value)})
        
        logger.debug(f"Returning dataframe with {len(df)} rows")
        return df
    
    @modguard.public
    def dbReport(
        self,
        input_values: List[str],
        input_db: Union[Input, Output],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ):
        taxon = self._validate_taxon_id(taxon)
        
        urls: list[str] = []
        for i in range(0, len(input_values), self._chunk_size):
            urls.append(self._url + "?method=dbreport&format=row")
            urls[-1] += f"&input={input_db.value.replace(' ', '').lower()}"
            urls[-1] += f"inputValues={','.join(input_values[i:i + self._chunk_size])}"
            urls[-1] += f"&taxonId={taxon}"
        
        return NotImplementedError
    
    @modguard.public
    def dbFind(
        self,
        input_values: List[str],
        output_db: Union[Output, List[Output]],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        if isinstance(output_db, Output):
            output_db = [output_db]
        
        taxon = self._validate_taxon_id(taxon)
        
        urls: list[str] = []
        for out_db in output_db:
            for i in range(0, len(input_values), self._chunk_size):
                urls.append(self._url + "?method=dbfind&format=row")
                urls[
                    -1
                ] += f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
                urls[-1] += f"&output={out_db.value}"
                urls[-1] += f"&taxonId={taxon}"
        
        json_result = self._execute(urls, as_dataframe=False)
        master_df: pd.DataFrame = pd.DataFrame(json_result[0])
        for result in json_result[1:]:
            df = pd.DataFrame(result)
            master_df = pd.merge(
                master_df,
                df,
                on=["InputValue", "Input Type"],
                how="inner",
                validate="one_to_one",
            )
        return master_df
    
    @modguard.public
    def dbOrtho(
        self,
        input_values: list[str],
        input_db: Input,
        output_db: Union[Output, List[Output]],
        input_taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
        output_taxon: Union[Taxon, int] = Taxon.MUS_MUSCULUS,
    ):
        input_taxon, output_taxon = self._validate_taxon_id([input_taxon, output_taxon])
        input_taxon: int = input_taxon.value if isinstance(input_taxon, Taxon) else input_taxon
        output_taxon: int = output_taxon.value if isinstance(output_taxon, Taxon) else output_taxon
        
        if isinstance(output_db, Output):
            output_db = [output_db]
        
        urls: list[str] = []
        for out_db in output_db:
            for i in range(0, len(input_values), self._chunk_size):
                urls.append(self._url + "?method=dbortho")
                urls[-1] += f"&input={input_db.value.replace(' ', '').lower()}"
                urls[
                    -1
                ] += f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
                urls[-1] += f"&inputTaxon={input_taxon}"
                urls[-1] += f"&outputTaxon={output_taxon}"
                urls[-1] += f"&output={out_db.value.replace(' ', '').lower()}"
                urls[-1] += "&format=row"
        
        json_results: List[dict] = self._execute(urls, as_dataframe=False)
        master_df: pd.DataFrame = pd.DataFrame(json_results[0])
        for i, result in enumerate(json_results):
            df = pd.DataFrame(result)
            master_df = pd.merge(
                master_df, df, on=["InputValue"], how="inner", validate="one_to_one"
            )
        
        # Remove potential duplicate columns
        for column in master_df.columns:
            if str(column).endswith("_x"):
                master_df = master_df.drop(column, axis=1)
            elif str(column).endswith("_y"):
                master_df.rename(columns={column: column[:-2]}, inplace=True)
        
        master_df.rename(columns={"InputValue": input_db.value}, inplace=True)
        
        return master_df
    
    @modguard.public
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
        
        taxon = self._validate_taxon_id(taxon)
        
        annotations = [a.replace(" ", "").lower() for a in annotations]
        urls: list[str] = []
        for i in range(0, len(input_values), self._chunk_size):
            urls.append(self._url + "?method=dbannot")
            urls[-1] += f"&inputValues={','.join(input_values[i:i + self._chunk_size])}"
            urls[-1] += f"&taxonId={taxon}"
            urls[-1] += f"&annotations={','.join(annotations)}"
            urls[-1] += "&format=row"
        
        df = self._execute(urls)
        df = df.rename(columns={"InputValue": "Input Value"})
        return df
    
    @modguard.public
    def dbOrg(
        self,
        input_db: Input,
        output_db: Output,
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS,
    ) -> pd.DataFrame:
        taxon = self._validate_taxon_id(taxon)
        
        input_db_val = input_db.value.replace(" ", "_")
        output_db_val = output_db.value.replace(" ", "_")
        
        url = f"https://biodbnet-abcc.ncifcrf.gov/db/dbOrgDwnld.php?file={input_db_val}__to__{output_db_val}_{taxon}"
        buffer = io.StringIO(self._http.get_text(url))
        return pd.read_csv(
            buffer, sep="\t", header=None, names=[input_db.value, output_db.value]
        )


if __name__ == "__main__":
    biodbnet = BioDBNet(cache=False, show_progress=True)
    result = biodbnet.dbOrtho(
        input_values=["4318", "1376", "2576", "10089"],
        input_db=Input.GENE_ID,
        output_db=Output.GENE_SYMBOL,
        input_taxon=Taxon.HOMO_SAPIENS,
        output_taxon=Taxon.MUS_MUSCULUS
    )
    print(result)
