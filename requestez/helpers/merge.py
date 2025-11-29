from typing import List, Dict, Tuple, Set, Union, Any

def merge(*args: Any) -> Union[List, Dict, str, Tuple, Set]:
    """
    Merges lists, tuples, dictionaries, strings, and sets.
    The type of the returned object is determined by the first argument.
    
    - Lists/Tuples: Concatenated.
    - Dictionaries: Merged (later arguments override earlier ones).
    - Strings: Joined with a space.
    - Sets: Union.
    
    :param args: Objects to merge.
    :return: Merged object.
    :raises TypeError: If arguments are of incompatible types.
    """
    if not args:
        return args

    obj = args[0]
    obj_type = type(obj)
    
    # Validate types
    for arg in args:
        if not isinstance(arg, (obj_type, list, tuple)) and not (isinstance(obj, (list, tuple)) and isinstance(arg, (list, tuple))):
             # Allow mixing list and tuple if target is list/tuple?
             # The original code allowed mixing list and tuple somewhat.
             if not isinstance(arg, obj_type):
                 raise TypeError(f"Cannot merge {obj_type} with {type(arg)}")

    if isinstance(obj, str):
        return " ".join(args)
    
    elif isinstance(obj, list):
        merged_list = []
        for arg in args:
            merged_list.extend(list(arg))
        return merged_list
        
    elif isinstance(obj, tuple):
        merged_list = []
        for arg in args:
            merged_list.extend(list(arg))
        return tuple(merged_list)
        
    elif isinstance(obj, dict):
        merged_dict = {}
        for arg in args:
            merged_dict.update(arg)
        return merged_dict
        
    elif isinstance(obj, set):
        merged_set = set()
        for arg in args:
            merged_set.update(arg)
        return merged_set
        
    else:
        raise TypeError(f"Unsupported type for merge: {obj_type}")
