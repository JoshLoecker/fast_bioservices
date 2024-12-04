from __future__ import annotations

import json

from fast_bioservices.fast_http import _AsyncHTTPClient


class _NCBI(_AsyncHTTPClient):
    def __init__(self, *, cache: bool, api_key: str):
        """Access to NCBI V2 Datasets.

        API documentation: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/rest-api

        How to create an API key: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/api-keys/

        :param cache: Should cache be used.
        :param api_key: an optional API key.
        """
        self._chunk_size: int = 5
        self._url: str = "https://api.ncbi.nlm.nih.gov/datasets/v2"
        self._max_requests_per_second: int = 5 if api_key == "" else 10
        self._api_key: str = api_key

        super().__init__(cache=cache, max_requests_per_second=self._max_requests_per_second)

    def _create_chunks(self, items: list[str]) -> list[str]:
        return [",".join(items[i : i + self._chunk_size]) for i in range(0, len(items), self._chunk_size)]

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, value: int):
        self._api_key = value
        if value != "":
            self.update_rate_limit(10)


class Gene(_NCBI):
    def __init__(self, cache: bool = True, api_key: str = ""):
        """Access gene-specific data of NCBI Datasets."""
        super().__init__(cache=cache, api_key=api_key)

    async def _parse_reports(self, queries: list[str]) -> dict[str, list]:
        results: dict[str, list] = {"gene": [], "product": [], "query": [], "warnings": [], "warning": [], "errors": []}
        for response in await self._get(queries, headers={"accept": "application/x-ndjson"}):
            response = response.rstrip(b"\n")
            for line in response.split(b"\n"):
                as_json = json.loads(line)
                for key in as_json:
                    results[key].append(as_json[key])

        return results

    async def report_by_id(self, gene_ids: int | str | list[int] | list[str] | list[int | str]) -> dict[str, list]:
        """Get gene-specific data by gene ID."""
        gene_ids = [gene_ids] if isinstance(gene_ids, (int, str)) else gene_ids
        for g in gene_ids:
            if not g.isdigit():
                raise TypeError(f"Input values should be a digit! Got a non-digit value: '{g}'")

        queries: list[str] = [
            f"{self._url}/gene/id/{chunk}?page_size={self._chunk_size}&returned_content=COMPLETE&api_key={self._api_key}"
            for chunk in self._create_chunks(gene_ids)
        ]
        return await self._parse_reports(queries)

    async def report_by_symbol(self, symbols: str | list[str], taxon: str) -> dict[str, list]:
        """Get gene-specific data by gene symbol."""
        symbols = [symbols] if isinstance(symbols, str) else symbols

        queries: list[str] = [
            f"{self._url}/gene/symbol/{chunk}/taxon/{taxon}?page_size={self._chunk_size}&returned_content=COMPLETE"
            for chunk in self._create_chunks(symbols)
        ]
        return await self._parse_reports(queries)
