import concurrent.futures
import os
from typing import Union

import pandas as pd
import tqdm.contrib.concurrent

from fast_bioservices.log import logger
from fast_bioservices.nodes import Input, Output, Taxon
from fast_bioservices.utils import HTTP, flatten


class BioDBNet:
    _url = "https://biodbnet-abcc.ncifcrf.gov/webServices/rest.php/biodbnetRestApi.json"
    
    def __init__(
        self,
        max_workers: int = min(32, os.cpu_count() + 4),
        show_progress: bool = True,
        cache: bool = True,
    ):
        self._chunk_size: int = 100
        self._max_workers: int = max_workers
        self._http = HTTP(cache=cache)
        self._show_progress = show_progress
    
    def _execute(self, urls: list[str]) -> pd.DataFrame:
        logger.debug(f"Collecting information for {len(urls)} sets of urls")
        
        if self._show_progress:
            results = tqdm.contrib.concurrent.thread_map(self._http.get_json, urls, max_workers=self._max_workers)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                results = list(executor.map(self._http.get_json, urls))
        
        flat_results = flatten(results)
        return pd.DataFrame(flat_results)
    
    def _are_databases_valid(self, input: Input, output: Union[Output, list[Output]]) -> bool:
        """
        The input database and output database must be different.
        :param input: The input database.
        :type input: Input
        :param output: The output database.
        :type output: Union[Output, list[Output]]
        :return: True if the input and output databases are different, False otherwise.
        :rtype: bool
        """
        logger.debug("Validating databases")
        database_url: str = f"{self._url}?method=getoutputsforinput&input={input.value}"
        valid_outputs: list[str] = self._http.get_json(database_url)["output"]
        return all([o.value in valid_outputs for o in output])
    
    def _taxon_id_valid(self, taxon: int) -> bool:
        logger.debug("Validating taxon ID")
        taxon_url: str = "https://www.ncbi.nlm.nih.gov/taxonomy/?term={}".format(taxon)
        if "No items found." in self._http.get_text(taxon_url):
            return False
        return True
    
    def db2db(
        self,
        input_db: Input,
        output_db: Union[Output, list[Output]],
        input_values: list[str],
        taxon: Union[Taxon, int] = Taxon.HOMO_SAPIENS
    ) -> pd.DataFrame:
        taxon: int = taxon.value if isinstance(taxon, Taxon) else taxon
        if not self._are_databases_valid(input_db, output_db):
            raise ValueError(
                "You have provided an invalid output database(s).\nA common result of this problem is including the input database as an output database")
        logger.debug("Databases are valid")
        
        if not self._taxon_id_valid(taxon):
            raise ValueError(f"Taxon ID of '{taxon}' is not valid")
        logger.debug("Taxon ID is valid")
        
        input_db = input_db.value
        if isinstance(output_db, Output):
            output_db = [output_db]
        output_db = ",".join([o.value for o in output_db])
        logger.debug(f"Got an input database with a value of '{input_db}'")
        logger.debug(f"Got {len(output_db.split(','))} output databases with values of: {output_db}")
        
        urls: list[str] = []
        for i in range(0, len(input_values), self._chunk_size):
            urls.append(self._url + "?method=db2db")
            urls[-1] += "&input={}".format(input_db)
            urls[-1] += "&outputs={}".format(output_db)
            urls[-1] += "&inputValues={}".format(",".join(input_values[i:i + self._chunk_size]))
            urls[-1] += "&taxonId={}".format(taxon)
            urls[-1] += "&format={}".format("row")
        
        df = self._execute(urls)
        df.rename(columns={"InputValue": input_db}, inplace=True)
        logger.debug(f"Returning dataframe with {len(df)} rows")
        return df


if __name__ == '__main__':
    biodbnet = BioDBNet(cache=True, show_progress=False)
    df = biodbnet.db2db(
        Input.GENE_ID, [Output.GENE_SYMBOL, Output.ENSEMBL_GENE_ID],
        [str(i) for i in range(1000)],
        Taxon.HOMO_SAPIENS,
    )
    print(df)
