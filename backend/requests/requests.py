from typing import Dict
import json
from utils.errors import ValidationError, BottomOfRequestError
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


class Request:
    def __init__(self, request_data: bytes):
        try:
            self._request_data = Request._decode_request(request_data)
        except Exception as _:
            raise ValidationError("Poorly formatted request. Could not parse the request data.")
        self._consumable_path = self._request_data["request"]

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
        if not _validate_request_path(self.request_path):
            raise ValidationError("Requested path is not legal")
        return True

    def extract_next_route(self) -> str:
        """
        Gives the next route, and removes it from the consumable path
        :return: next route
        """
        chunks = self._consumable_path.split(".")
        if len(chunks) == 0 or (len(chunks) == 1 and len(chunks[0]) == 0):
            raise BottomOfRequestError()
        next_route = chunks[0]
        self._consumable_path = '.'.join(chunks[1:])
        return next_route

    @property
    def request_path(self):
        return self._request_data["request"]


if __name__ == "__main__":
    print(_validate_request_path("a.0aa_.bbbb"))
