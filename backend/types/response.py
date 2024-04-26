from typing import Dict
from utils.constants import *
from utils.errors import *


class Response:
    def __init__(self, data: Dict):
        self.__dict__.update(data)
        if "status_code" not in data:
            raise InternalResponseError("No status code provided for response")
