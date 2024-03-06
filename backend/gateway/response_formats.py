from utils.constants import *
from utils.errors import InternalResponseError
import json


class Response:
    """
    Manages responses, and ensures that they are formatted uniformly
    """
    def __init__(self, status_code, **kwargs):
        assert status_code in [SUCCESS, POOR_FORMAT, REJECTED_BY_ENTITY, ROUTE_DNE], "Invalid status code"
        self.status_code = status_code
        self.kwargs = kwargs
        self._validate_response()

    def _validate_response(self):
        if self.status_code == SUCCESS:
            if "data" not in self.kwargs:
                raise InternalResponseError("Missing data in a success response")
        if self.status_code in [POOR_FORMAT, REJECTED_BY_ENTITY, ROUTE_DNE]:
            if "error" not in self.kwargs:
                raise InternalResponseError("Missing error in a error response")

    def get_bytes(self) -> bytes:
        _response = {
            "statusCode": self.status_code,
            **self.kwargs
        }
        return json.dumps(_response, indent=4).encode()


if __name__ == "__main__":
    response = Response(status_code=SUCCESS, data={"hello":"world"})
    print(response.get_bytes().decode())
