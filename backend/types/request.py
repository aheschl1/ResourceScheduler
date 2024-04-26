from typing import Dict

from backend.utils.constants import *
from utils.errors import *


class Request:
    def __init__(self, data: Dict):
        if "method" not in data or data["method"] not in [GET, POST, DELETE, PUT]:
            raise InternalResponseError("Invalid request method")
        if "authorization" not in data:
            raise InvalidRequestError("No authorization provided in request")
        self._raw_data = data

    def get_raw_data(self):
        return self._raw_data


class GETRequest(Request):
    """
    Request intended to query data about an entity
    """

    def __init__(self, data: Dict):
        super().__init__(data)
        if data["method"] != GET:
            raise InternalResponseError("Invalid request method")


class POSTRequest(Request):
    """
    Request intended to add things to existing collections
    1. Request resources for a client
    2. Add entity to existing organization
    """

    def __init__(self, data: Dict):
        super().__init__(data)
        if data["method"] != POST:
            raise InternalResponseError("Invalid request method")


class PUTRequest(Request):
    """
    Creating new things
    1. New organization
    """

    def __init__(self, data: Dict):
        super().__init__(data)
        if data["method"] != PUT:
            raise InternalResponseError("Invalid request method")


class DELETERequest(Request):
    """
    Request intended to modify/delete content
    """

    def __init__(self, data: Dict):
        super().__init__(data)
