import concurrent.futures
import functools
from abc import ABC, abstractmethod
from typing import Callable, Sequence

from rich.progress import BarColumn, Progress, TaskID, TimeRemainingColumn

from fast_bioservices.log import logger


class BaseModel(ABC):
    def __init__(self, max_workers: int, show_progress: bool):
        self._max_workers: int = max_workers
        self._show_progress: bool = show_progress

    @property
    @abstractmethod
    def url(self) -> str: ...

    def _execute(self, func: Callable, data: Sequence):
        def with_progress(func: Callable, url: str, progress_bar: Progress, task: TaskID):
            result = func(url).json
            progress_bar.update(task, advance=1)
            return result

        if self._show_progress:
            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                "{task.completed}/{task.total} batches",
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task("[cyan]Working...", total=len(data))
                with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                    partial = functools.partial(with_progress, func=func, progress_bar=progress, task=task)
                    results = list(executor.map(partial, data))
                progress.update(task, description="[cyan]Working... Done!")
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                results = list(executor.map(func, data))
                results = [r.json for r in results]

        return results
