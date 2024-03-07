import re


def validate_iso8601(time: str):
    regex = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
    try:
        match_iso8601 = re.compile(regex).match
        if match_iso8601(time) is not None:
            return True
    except:
        pass
    return False
