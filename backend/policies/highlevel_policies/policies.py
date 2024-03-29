from typing import Tuple, List

from backend.policies.policy import Policy
from backend.requests.requests import Request
from backend.utils.utils import validate_iso8601


class TicketedPolicy(Policy):
    """
    High Level Policy
    """

    def validate(self, request: Request) -> Tuple[bool, str]:
        if "quantity" not in request.data:
            return False, "Missing required header: quantity"
        if "request_parameters" not in request.data:
            return False, "Missing required header: request_parameters"
        if not isinstance(request.data["request_parameters"], dict):
            return False, "Expected request_headers to be a dictionary"
        return True, "success"


class TimeslotPolicy(Policy):
    """
    High Level Policy
    """

    @staticmethod
    def _validate_data_headers(request: Request) -> Tuple[bool, List[str]]:
        missing_headers = []
        if "start_time" not in request.data:
            missing_headers.append("start_time")
        if "end_time" not in request.data:
            missing_headers.append("end_time")
        return len(missing_headers) == 0, missing_headers

    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Checks that data has start_time and end_time.
        Checks that time stamps are valid (iso8601 format)
        Checks that start time < end time
        :param request:
        :return:
        """
        header_approval, missing_headers = TimeslotPolicy._validate_data_headers(request)
        if not header_approval:
            return False, f"Missing required headers: {missing_headers}."
        valid_timestamp = validate_iso8601(request.data["start_time"])
        valid_timestamp = valid_timestamp and validate_iso8601(request.data["end_time"])
        if not valid_timestamp:
            return False, f"Timestamps must be in ISO 8601 format, but were not."
        if request.data["end_time"] <= request.data["start_time"]:
            return False, f"End time must be greater than start time."
        return True, "success"
