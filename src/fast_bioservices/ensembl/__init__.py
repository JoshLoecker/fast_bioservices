from fast_bioservices.base import BaseModel
from fast_bioservices.fast_http import FastHTTP


class Ensembl(BaseModel, FastHTTP):
    def __init__(
        self,
        max_workers: int,
        show_progress: bool,
        cache: bool = True,
    ):
        self._url = "https://rest.ensembl.org"
        self._max_workers: int = max_workers
        self._show_progress: bool = show_progress

        BaseModel.__init__(self, url=self._url)
        FastHTTP.__init__(
            self,
            cache=cache,
            max_workers=self._max_workers,
            max_requests_per_second=15,
            show_progress=self._show_progress,
        )

    @property
    def url(self) -> str:
        return self._url
