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
        self._path_fragments = self._request_data["request"].split(".")
        self._root_name = self._path_fragments[0]
        self._current_fragment = 0

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
        if self._current_fragment == len(self._path_fragments):
            raise BottomOfRequestError()
        next_route = self._path_fragments[self._current_fragment]
        self._current_fragment += 1
        return next_route

    @property
    def request_path(self):
        return self._request_data["request"]

    @property
    def root_name(self) -> str:
        return self._root_name

    @property
    def data(self) -> dict:
        return self._request_data["data"]


if __name__ == "__main__":
    print(_validate_request_path("a.0aa_.bbbb"))
