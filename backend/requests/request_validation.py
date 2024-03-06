from typing import Dict
import json
from utils.errors import ValidationError


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
        return True
