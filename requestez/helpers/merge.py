from typing import List, Dict, Iterable, Tuple, Set


def merge(*args: List or Dict or str or Tuple or Set) -> List or Dict or str or Tuple or Set:
    """
    merges lists, tuples, dictionaries, strings, lists and tuples

    '

    '

    the type of the returned object is the same as the first element passed as arg

    '

    '

    the dictionary returned has the value of the latter object in case of common keys

    i.e. the value in the latter arg is prioritised
    :param args:
    :return: type of first argument passed or an error message
    """
    if args:
        obj = args[0]
    else:
        return args
    merged: str or dict or tuple or list or set = "" if type(obj) == str else {} if type(obj) == dict else [] if type(
        obj) == list else tuple() if type(obj) == tuple else {} if type(obj) == set else "Unknown"
    for arg in args:
        if type(arg) != type(merged):
            if type(arg) == tuple and type(merged) == list:
                pass
            elif type(merged) == tuple and type(arg) == list:
                pass
            else:
                return "Merge not supported between some or all args"
    if obj == "Unknown":
        return "Unsupported merge type"
    if type(merged) == str:
        merged = " ".join(args)
    elif type(merged) == list:
        for arg in args:
            merged.extend(arg)
    elif type(merged) == tuple:
        merge_d = []
        for arg in args:
            merge_d.extend(list(arg))
        merged = tuple(merge_d)
    elif type(merged) == dict:
        for dictionary in args:
            merged.update(dictionary)
    return merged
