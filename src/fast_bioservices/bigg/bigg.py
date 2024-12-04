from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from fast_bioservices.fast_http import _AsyncHTTPClient


class BiGG(_AsyncHTTPClient):
    _download_url: str = "http://bigg.ucsd.edu/static/models"

    def __init__(self, cache: bool = True):
        """Access the BiGG database."""
        self._url: str = "http://bigg.ucsd.edu/api/v2"
        _AsyncHTTPClient.__init__(self, cache=cache, max_requests_per_second=10)

    @property
    def url(self) -> str:
        """Return the root URL."""
        return self._url

    @property
    def download_url(self) -> str:
        """Return the download-specific URL."""
        return self._download_url

    async def version(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        """Get the BiGG database version."""
        response = (await self._get(f"{self.url}/database_version", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def models(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        """Get a list of all models."""
        response = (await self._get(f"{self.url}/models", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def model_details(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        """Get details of all models."""
        response = (await self._get(f"{self.url}/models/{model_id}", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def json(self, model_id: str, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        """Download model details in JSON format."""
        response = (await self._get(f"{self.url}/models/{model_id}/download", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def download(
        self,
        model_id: str,
        ext: Literal["json", "xml", "mat", "json.gz", "xml.gz", "mat.gz"],
        download_path: Path | None = None,
        temp_disable_cache: bool = False,
    ) -> None:
        """Download a model in a given format."""
        if download_path is None:
            download_path = f"{model_id}.{ext}"
        elif not download_path.as_posix().endswith(f"{model_id}.{ext}"):
            download_path = download_path / f"{model_id}.{ext}"

        response = (await self._get(f"{self.download_url}/{model_id}.{ext}", temp_disable_cache=temp_disable_cache))[0]

        if ext == "json":
            json.dump(response, download_path.open("w"), indent=2)  # type: ignore
        else:
            with download_path.open("w") as o_stream:
                o_stream.write(response.decode())

    async def model_reactions(
        self,
        model_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        """Get a list of model reactions."""
        response = (await self._get(f"{self.url}/models/{model_id}/reactions", temp_disable_cache=temp_disable_cache))[
            0
        ]
        return json.loads(response)

    async def model_reaction_details(
        self,
        model_id: str,
        reaction_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        """Get a detailed list of model reactions."""
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
        """Get a list of model metabolites."""
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
        """Get a detailed list of model metabolites."""
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
        """Get a list of model genes."""
        response = (await self._get(f"{self.url}/models/{model_id}/genes", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def model_gene_details(
        self,
        model_id: str,
        gene_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        """Get a detailed list of model genes."""
        response = (
            await self._get(
                f"{self.url}/models/{model_id}/genes/{gene_id}",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)

    async def universal_reactions(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        """Get a list of universal reactions."""
        response = (await self._get(f"{self.url}/universal/reactions", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def universal_reaction_details(
        self,
        reaction_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        """Get a detailed list of universal reactions."""
        response = (
            await self._get(
                f"{self.url}/universal/reactions/{reaction_id}",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)

    async def universal_metabolites(self, temp_disable_cache: bool = False) -> Mapping[Any, Any]:
        """Get a list of universal metabolites."""
        response = (await self._get(f"{self.url}/universal/metabolites", temp_disable_cache=temp_disable_cache))[0]
        return json.loads(response)

    async def universal_metabolite_details(
        self,
        metabolite_id: str,
        temp_disable_cache: bool = False,
    ) -> Mapping[Any, Any]:
        """Get a detailed list of universal metabolites."""
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
        """Search for a given query."""
        response = (
            await self._get(
                f"{self.url}/search?query={query}&search_type={search_type}",
                temp_disable_cache=temp_disable_cache,
            )
        )[0]
        return json.loads(response)
