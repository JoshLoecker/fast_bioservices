import json
from typing import Any, Literal, Mapping, Optional

from fast_bioservices.fast_http import _AsyncHTTPClient


class BiGG(_AsyncHTTPClient):
    _download_url: str = "http://bigg.ucsd.edu/static/models"

    def __init__(self, cache: bool = True):
        self._url: str = "http://bigg.ucsd.edu/api/v2"
        _AsyncHTTPClient.__init__(self, cache=cache, max_requests_per_second=10)

    @property
    def url(self) -> str:
        return self._url

    @property
    def download_url(self) -> str:
        return self._download_url

    async def version(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        response = (await self._get(f"{self.url}/database_version", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def models(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        response = (await self._get(f"{self.url}/models", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def model_details(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (await self._get(f"{self.url}/models/{model_id}", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def json(self, model_id: str, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        response = (await self._get(f"{self.url}/models/{model_id}/download", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def download(
        self,
        model_id: str,
        ext: Literal["json", "xml", "mat", "json.gz", "xml.gz", "mat.gz"],
        download_path: Optional[str] = None,
        temp_disable_cache: bool = False,
    ) -> None:
        if download_path is None:
            download_path = f"{model_id}.{ext}"
        elif not download_path.endswith(f"{model_id}.{ext}"):
            download_path = f"{download_path}/{model_id}.{ext}"

        response = await self._get(f"{self.download_url}/{model_id}.{ext}", temp_disable_cache=temp_disable_cache)

        if ext == "json":
            json.dump(response[0], open(download_path, "w"), indent=2)  # type: ignore
        else:
            with open(download_path, "wb") as o_stream:
                o_stream.write(response[0])

    async def model_reactions(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (await self._get(f"{self.url}/models/{model_id}/reactions", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def model_reaction_details(
        self,
        model_id: str,
        reaction_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (
            await self._get(
                f"{self.url}/models/{model_id}/reactions/{reaction_id}",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)

    async def model_metabolites(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (
            await self._get(
                f"{self.url}/models/{model_id}/metabolites",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)

    async def model_metabolite_details(
        self,
        model_id: str,
        metabolite_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (
            await self._get(
                f"{self.url}/models/{model_id}/metabolites/{metabolite_id}",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)

    async def model_genes(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (await self._get(f"{self.url}/models/{model_id}/genes", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def model_gene_details(
        self,
        model_id: str,
        gene_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (
            await self._get(
                f"{self.url}/models/{model_id}/genes/{gene_id}",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)

    async def universal_reactions(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        response = (await self._get(f"{self.url}/universal/reactions", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def universal_reaction_details(
        self,
        reaction_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (
            await self._get(
                f"{self.url}/universal/reactions/{reaction_id}",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)

    async def universal_metabolites(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        response = (await self._get(f"{self.url}/universal/metabolites", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def universal_metabolite_details(
        self,
        metabolite_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (
            await self._get(
                f"{self.url}/universal/metabolites/{metabolite_id}",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)

    async def search(
        self,
        query: str,
        search_type: Literal["metabolites", "genes", "models", "reactions"],
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        response = (
            await self._get(
                f"{self.url}/search?query={query}&search_type={search_type}",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)
