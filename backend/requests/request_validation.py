from typing import Dict
import json
from utils.errors import ValidationError
import re


def _validate_request_path(path: str) -> bool:
    """
    Is the path valid?
    Can not start with dot
    Can not end with dot
    Can have numbers, letters, and underscore
    Can not have two dots in a raw
    :param path:
    :return:
    """
    regex = re.compile(r'^[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*$')
    return regex.match(path) is not None


class RequestParser:
    def __init__(self, request_data: bytes):
        try:
            self._request_data = RequestParser._decode_request(request_data)
        except Exception as _:
            raise ValidationError("Poorly formatted request. Could not parse the request data.")

    @staticmethod
    def _decode_request(req: bytes) -> Dict:
        """
        Given bytes, returns the dictionary.
        Throws a json format error
        :param req:
        :return:
        """
        return json.loads(req.decode())

    def validate(self) -> True:
        if not self._request_data:
            raise ValidationError("Request data is None")
        if "authorization" not in self._request_data:
            raise ValidationError("Request does not have an authorization key")
        if "request" not in self._request_data:
            raise ValidationError("Request path not specified in request")
        if "data" not in self._request_data:
            raise ValidationError("Request missing data arguments")
        if not _validate_request_path(self._request_data["request"]):
            raise ValidationError("Requested path is not legal")
        return True


if __name__ == "__main__":
    print(_validate_request_path("a.0aa_.bbbb"))
