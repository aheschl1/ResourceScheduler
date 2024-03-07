from typing import Tuple, List, Union, Dict

from backend.requests.requests import Request
from backend.utils.utils import validate_iso8601


class Policy:
    def __init__(self, full_approval: bool = False):
        self.full_approval = full_approval

    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Validate a request against a policy
        :param request: The request to validate
        :return: Approved or not, and reason if failure
        """
        if not self.full_approval:
            return False, "Base class policy without full approval auto rejects."
        return True, "success"


class TimeslotPolicy(Policy):

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


class CascadedPolicy(Policy):
    def __init__(self, cascaded_policies: List[Union[str, List, Dict]]):
        super().__init__(False)
        self.cascaded_policies = [PolicyFactory.get_policy_from_argument(x) for x in cascaded_policies]

    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Validated request against a list of cascaded policies
        :param request:
        :return:
        """
        result, reasons = True, []
        for policy in self.cascaded_policies:
            p_result, reason = policy.validate(request)
            if not p_result:
                reasons.append(reason)
                result = False
        return result, str(reasons)


class PolicyFactory:
    @staticmethod
    def create_full_approval_policy() -> Policy:
        return Policy(full_approval=True)

    @staticmethod
    def get_cascade_policy_from_list(arg: List) -> Policy:
        return CascadedPolicy(arg)

    @staticmethod
    def get_policy_from_argument(arg: Union[str,Dict,List]) -> Policy:
        if isinstance(arg, str):
            return PolicyFactory.get_policy_from_name(arg)
        if isinstance(arg, list):
            return PolicyFactory.get_cascade_policy_from_list(arg)
        raise NotImplementedError("Only string policy names and lists of names are implemented right now")

    @staticmethod
    def get_policy_from_name(name: str) -> Policy:
        mapping = {
            "FullApproval": PolicyFactory.create_full_approval_policy,
            "BasicTimeslot": TimeslotPolicy
        }
        return mapping[name]
