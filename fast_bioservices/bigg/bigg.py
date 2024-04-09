from typing import Any, List, Mapping, Union

from fast_bioservices.base import BaseModel
from fast_bioservices.fast_http import FastHTTP

"""
APIs available

- Download models
    - JSON
    - XML
    - MAT
- List of all models
- Model details
- Model reactions
- Details of model reactions
- Model metabolites
- Details of model metabolites
- Model genes
- Details of model genes
- Universal reactions
- Details of universal reactions
- Universal metabolites
- Details of universal metabolites
- Universal genes (May not exist)
- Details of universal genes (May not exist)
- Search query


"""


class BiGG(BaseModel, FastHTTP):
    _url: str = "http://bigg.ucsd.edu/api/v2"

    def __init__(self, cache: bool = True, show_progress: bool = True):
        # Initialize parent classes
        BaseModel.__init__(self, show_progress=show_progress)
        FastHTTP.__init__(self, cache=cache, max_requests_per_second=10)

    @property
    def url(self) -> str:
        return self._url

    @property
    def version(self) -> Mapping[Any, Any]:
        return self.get(f"{self.url}/database_version", temp_disable_cache=True).json()

    @property
    def models(self) -> Mapping[Any, Any]:
        return self.get(f"{self.url}/models", temp_disable_cache=True).json()


if __name__ == "__main__":
    bigg = BiGG()
    print(bigg.version)
