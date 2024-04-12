from typing import Dict, Tuple
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
        raw_data = request_data.decode()
        self.request_method, request_data = Request._decode_http(raw_data)
        try:
            self._request_data = Request._decode_request(request_data)
        except Exception as _:
            raise ValidationError("Poorly formatted request. Could not parse the request data.")
        self._path_fragments = self._request_data["entity"].split(".")
        self._root_name = self._path_fragments[0]
        self._current_fragment = 0

    @staticmethod
    def _decode_http(raw_data: str) -> Tuple[str, str]:
        lines = raw_data.split("\r\n")
        # assert correct header line
        top_headers = lines[0].split(" ")
        if top_headers[1] != "/":
            raise ValidationError("Server only supports root HTTP query.")
        if top_headers[2] != "HTTP/1.1":
            raise ValidationError("Only HTTP/1.1 is supported.")
        # first line, first word is the request method
        method = top_headers[0]
        if method not in ["GET", "POST", "PUT"]:
            raise ValidationError("Unsupported method. Use GET to query on resources, POST to register a resource, and PUT to create an entity/organization")

        content = raw_data.split("\r\n\r\n")[-1]
        return method, content

    @staticmethod
    def _decode_request(req: str) -> Dict:
        """
        Given bytes, returns the dictionary.
        Throws a json format error
        :param req:
        :return:
        """
        return json.loads(req)

    def validate(self) -> True:
        if not self._request_data:
            raise ValidationError("Request data is None")
        if "entity" not in self._request_data:
            raise ValidationError("Entity path not specified in request")
        if not _validate_request_path(self.entity_path):
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
    def entity_path(self):
        return self._request_data["entity"]

    @property
    def root_name(self) -> str:
        return self._root_name

    @property
    def data(self) -> dict:
        return self._request_data["data"]

    @property
    def raw_request(self) -> dict:
        return self._request_data

    @property
    def current_name(self):
        return self._path_fragments[self._current_fragment - 1]

    @property
    def headers(self):
        return list(self._request_data.keys())


if __name__ == "__main__":
    print(_validate_request_path("a.0aa_.bbbb"))
