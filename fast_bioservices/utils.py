def flatten(lists: list) -> list:
    data = []
    for item in lists:
        if isinstance(item, list):
            data.extend(flatten(item))
        else:
            data.append(item)
    return data
