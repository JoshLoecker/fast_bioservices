from difflib import SequenceMatcher
from typing import List, Union


def flatten(lists: list) -> list:
    data = []
    for item in lists:
        if isinstance(item, list):
            data.extend(flatten(item))
        else:
            data.append(item)
    return data


def fuzzy_search(query: str, possibilities: Union[str, List[str]]) -> float:
    matcher = SequenceMatcher(isjunk=None, a=query)
    if isinstance(possibilities, str):
        possibilities = [possibilities]

    # Provide a default value for the ratio
    ratios: list[float] = [0.0]
    for possible in possibilities:
        matcher.set_seq2(possible)
        ratios.append(matcher.ratio())
    return max(ratios)
