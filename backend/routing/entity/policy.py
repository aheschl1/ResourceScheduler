from abc import abstractmethod, ABC
from typing import Tuple, List, Union, Dict, Callable

from backend.requests.requests import Request
from backend.utils.utils import validate_iso8601


class Policy:
    def __init__(self, full_approval: bool = False):
        self.full_approval = full_approval

    @abstractmethod
    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Validate a request against a policy
        :param request: The request to validate
        :return: Approved or not, and reason if failure
        """
        if not self.full_approval:
            return False, "Base class policy without full approval auto rejects."
        return True, "success"


class TicketedPolicy(Policy):

    def validate(self, request: Request) -> Tuple[bool, str]:
        if "quantity" not in request.data:
            return False, "Missing required header: quantity"
        if "request_parameters" not in request.data:
            return False, "Missing required header: request_parameters"
        if not isinstance(request.data["request_parameters"], dict):
            return False, "Expected request_headers to be a dictionary"
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
    def __init__(self, cascaded_policies: List[Union[str, Policy, List, Dict]]):
        super().__init__(False)
        policies = []
        for p in cascaded_policies:
            if isinstance(p, Policy):
                policies.append(p)
            else:
                policies.append(PolicyFactory.get_policy_from_argument(p))
        self.cascaded_policies = policies

    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Validated request against a list of cascaded policies
        :param request:
        :return:
        """
        print(self.cascaded_policies)
        result, reasons = True, []
        for policy in self.cascaded_policies:
            p_result, reason = policy.validate(request)
            if not p_result:
                reasons.append(reason)
                result = False
        return result, str(reasons)


class RequiredHeaderPolicy(Policy):
    def __init__(self, arg: Dict):
        super().__init__(False)
        if "headers" not in arg:
            raise NotImplementedError("Policy is invalid")
        self.required_headers = arg["headers"]
        self.strict = arg.get("strict", False)

    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Validates headers exist, and only those specified if strict
        :param request:
        :return:
        """
        for header in self.required_headers:
            if '.' not in header:
                if header not in request.headers:
                    return False, f"Missing header {header}"
            else:
                # asked for say data.quantity to exist
                hierarchy = header.split('.')
                level = request.raw_request
                for internal_header in hierarchy:
                    try:
                        level = level[internal_header]
                    except KeyError:
                        return False, f"Missing header {header}"

        if self.strict:
            for header in request.headers:
                if header not in self.required_headers:
                    return False, f"Header '{header}' not allowed"

        return True, "success"


class PolicyFactory:
    @staticmethod
    def create_full_approval_policy() -> Policy:
        return Policy(full_approval=True)

    @staticmethod
    def get_cascade_policy_from_list(arg: List) -> Policy:
        return CascadedPolicy(arg)

    @staticmethod
    def get_policy_from_dict(arg: Dict) -> Policy:
        policy_lookup = {
            "required_headers": RequiredHeaderPolicy
        }
        policies = []
        for key, value in arg.items():
            policies.append(policy_lookup[key](value))
        return CascadedPolicy(policies)

    @staticmethod
    def get_policy_from_argument(arg: Union[str, Dict, List]) -> Policy:
        if isinstance(arg, str):
            return PolicyFactory.get_policy_from_name(arg)
        if isinstance(arg, list):
            return PolicyFactory.get_cascade_policy_from_list(arg)
        if isinstance(arg, dict):
            return PolicyFactory.get_policy_from_dict(arg)
        raise NotImplementedError("Policy is invalid")

    @staticmethod
    def get_policy_from_name(name: str) -> Policy:
        mapping = {
            "FullApproval": PolicyFactory.create_full_approval_policy(),
            "BasicTimeslot": TimeslotPolicy(),
            "TicketedPolicy": TicketedPolicy()
        }
        if name not in mapping:
            raise NotImplementedError("Policy is invalid")

        return mapping[name]
