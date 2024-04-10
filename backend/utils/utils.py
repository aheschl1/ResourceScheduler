import re
from typing import Dict, Any


def validate_iso8601(time: str):
    regex = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
    try:
        match_iso8601 = re.compile(regex).match
        if match_iso8601(time) is not None:
            return True
    except:
        pass
    return False


def hierarchical_dict_lookup(dictionary: Dict[str, Any], key: str):
    """
    Looks up multi level keys.
    for example:
    {
        hi: {
            womp: womp2
        }
    }
    hi.womp = womp2
    :param dictionary:
    :param key:
    :return:
    """
    hierarchy = key.split('.')
    for internal_header in hierarchy:
        try:
            dictionary = dictionary[internal_header]
        except KeyError:
            raise KeyError(f"{key} not found in dictionary")
    return dictionary


def hierarchical_keys(dictionary: Dict[str, Any], parent_key=None):
    """
    Looks up multi level keys.
    for example:
    {
        hi: {
            womp: womp2
        }
    }
    returns hi and hi.womp
    :param parent_key:
    :param dictionary:
    :return:
    """
    non_dict_keys = []
    for key, value in dictionary.items():
        current_key = key if parent_key is None else f"{parent_key}.{key}"
        if isinstance(value, dict):
            non_dict_keys.extend(hierarchical_keys(value, current_key))
        non_dict_keys.append(current_key)
    return non_dict_keys


if __name__ == "__main__":
    d = {
        "a": "dw",
        "b": {
            "c": {
                "d": "fsd",
                "k": "dw"
            }
        }
    }
    print(hierarchical_keys(d))
