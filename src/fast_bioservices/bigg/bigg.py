import json
from typing import Any, Literal, Mapping, Optional

from fast_bioservices._base import BaseModel
from fast_bioservices._fast_http import FastHTTP


class BiGG(BaseModel, FastHTTP):
    _download_url: str = "http://bigg.ucsd.edu/static/models"

    def __init__(
        self,
        max_workers: int = 4,
        cache: bool = True,
        show_progress: bool = True,
    ):
        self._url: str = "http://bigg.ucsd.edu/api/v2"
        BaseModel.__init__(self, url=self._url)
        FastHTTP.__init__(
            self,
            cache=cache,
            workers=max_workers,
            show_progress=show_progress,
            max_requests_per_second=10,
        )

    @property
    def url(self) -> str:
        return self._url

    @property
    def download_url(self) -> str:
        return self._download_url

    def version(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        return self._get(f"{self.url}/database_version", temp_disable_cache=temp_disable_cache)[0].json

    def models(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        return self._get(f"{self.url}/models", temp_disable_cache=temp_disable_cache)[0].json

    def model_details(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(f"{self.url}/models/{model_id}", temp_disable_cache=temp_disable_cache)[0].json

    def json(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(
            f"{self.url}/models/{model_id}/download",
            temp_disable_cache=temp_disable_cache,
        )[0].json

    def download(
        self,
        model_id: str,
        format: Literal["json", "xml", "mat", "json.gz", "xml.gz", "mat.gz"],
        download_path: Optional[str] = None,
        temp_disable_cache: bool = False,
    ) -> None:
        if download_path is None:
            download_path = f"{model_id}.{format}"
        elif not download_path.endswith(f"{model_id}.{format}"):
            download_path = f"{download_path}/{model_id}.{format}"

        response = self._get(
            f"{self.download_url}/{model_id}.{format}",
            temp_disable_cache=temp_disable_cache,
        )

        if format == "json":
            json.dump(response[0].json, open(download_path, "w"), indent=2)
        else:
            with open(download_path, "wb") as o_stream:
                o_stream.write(response[0].bytes)

    def model_reactions(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(
            f"{self.url}/models/{model_id}/reactions",
            temp_disable_cache=temp_disable_cache,
        )[0].json

    def model_reaction_details(
        self,
        model_id: str,
        reaction_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(
            f"{self.url}/models/{model_id}/reactions/{reaction_id}",
            temp_disable_cache=temp_disable_cache,
        )[0].json

    def model_metabolites(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(
            f"{self.url}/models/{model_id}/metabolites",
            temp_disable_cache=temp_disable_cache,
        )[0].json

    def model_metabolite_details(
        self,
        model_id: str,
        metabolite_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(
            f"{self.url}/models/{model_id}/metabolites/{metabolite_id}",
            temp_disable_cache=temp_disable_cache,
        )[0].json

    def model_genes(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(f"{self.url}/models/{model_id}/genes", temp_disable_cache=temp_disable_cache)[0].json

    def model_gene_details(
        self,
        model_id: str,
        gene_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(
            f"{self.url}/models/{model_id}/genes/{gene_id}",
            temp_disable_cache=temp_disable_cache,
        )[0].json

    def universal_reactions(
        self, temp_disable_cache: bool = False
    ) -> Mapping[Any, Any]:
        return self._get(f"{self.url}/universal/reactions", temp_disable_cache=temp_disable_cache)[0].json

    def universal_reaction_details(
        self,
        reaction_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(
            f"{self.url}/universal/reactions/{reaction_id}",
            temp_disable_cache=temp_disable_cache,
        )[0].json

    def universal_metabolites(
        self, temp_disable_cache: bool = False
    ) -> Mapping[Any, Any]:
        return self._get(f"{self.url}/universal/metabolites", temp_disable_cache=temp_disable_cache)[0].json

    def universal_metabolite_details(
        self,
        metabolite_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(
            f"{self.url}/universal/metabolites/{metabolite_id}",
            temp_disable_cache=temp_disable_cache,
        )[0].json

    def search(
        self,
        query: str,
        search_type: Literal["metabolites", "genes", "models", "reactions"],
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        return self._get(
            f"{self.url}/search?query={query}&search_type={search_type}",
            temp_disable_cache=temp_disable_cache,
        )[0].json
