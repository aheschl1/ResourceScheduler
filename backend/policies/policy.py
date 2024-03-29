from abc import abstractmethod
from typing import Tuple, List, Union, Dict, Any

from backend.requests.requests import Request
from backend.utils.utils import validate_iso8601, hierarchical_dict_lookup


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

    def __str__(self):
        return str(self.__class__.__name__)

    def __call__(self, request: Request) -> Tuple[bool, str]:
        return self.validate(request)


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


# TODO cascaded policy verbose is a bit of a mess
class CascadedPolicy(Policy):
    def __init__(self, cascaded_policies: Union[Dict, List[Union[str, Policy, List, Dict]]]):
        super().__init__(False)
        policies = []
        if not isinstance(cascaded_policies, dict):
            for p in cascaded_policies:
                if isinstance(p, Policy):
                    policies.append(p)
                else:
                    policies.append(PolicyFactory.get_policy_from_argument(p))
        else:
            policies = PolicyFactory.get_policy_from_dict(cascaded_policies, return_policy_list=True)
        self.cascaded_policies = policies

    def validate(self, request: Request) -> Tuple[bool]:
        raise NotImplementedError("Server error. CascadePolicy is to be treated as abstract.")


class AndPolicy(CascadedPolicy):
    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Validated request against a list of cascaded policies
        :param request:
        :return:
        """
        result, reasons = True, []
        for policy in self.cascaded_policies:
            p_result, reason = policy.validate(request)
            reason = json.decoder.JSONDecoder().decode(reason)
            reasons.append({f"{str(policy)}": reason})
            if not p_result:
                result = False
        return result, json.dumps(reasons, indent=4)


class OrPolicy(CascadedPolicy):
    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Validated request against a list of policies.
        Only one policy must accept
        :param request:
        :return:
        """
        result, reasons = False, []
        for policy in self.cascaded_policies:
            p_result, reason = policy.validate(request)
            reason = json.decoder.JSONDecoder().decode(reason)
            reasons.append({f"{str(policy)}": reason})
            if p_result:
                result = True
                break

        return result, json.dumps(reasons, indent=4)


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
                try:
                    hierarchical_dict_lookup(request.raw_request, header)
                except KeyError:
                    return False, f"Missing header {header}"

        if self.strict:
            for header in request.headers:
                if header not in self.required_headers:
                    return False, f"Header '{header}' not allowed"

        return True, "success"


class ArgumentFormatPolicy(Policy):
    def __init__(self, requirements: Dict[str, str]):
        super().__init__(False)
        self.requirements = requirements
        self._formats = {
            "iso8601": validate_iso8601
        }

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key, format in self.requirements.items():
            value = hierarchical_dict_lookup(request.raw_request, key)
            try:
                validator = self._formats[format]
            except KeyError:
                return False, f"Unknown/Unimplemented format '{format}'"
            in_format = validator(value)
            reasons.append({f"{key}": in_format})
            if not in_format:
                result = False

        return result, json.dumps(reasons, indent=4)


class EqualityPolicy(Policy):
    def __init__(self, required_equality_keys: List[str]):
        super().__init__(False)
        self.required_equality_keys = required_equality_keys

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reason = True, "success"
        last_value = None
        for key in self.required_equality_keys:
            value = hierarchical_dict_lookup(request.raw_request, key)
            result = last_value is None or value == last_value
            last_value = value
            if not result:
                reason = f"Value '{key}' broke the equality chain"
                break
        return result, json.dumps(reason, indent=4)


class GreaterThanPolicy(Policy):
    def __init__(self, arguments: Dict[str, Any]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key, compare in self.arguments.items():
            value = hierarchical_dict_lookup(request.raw_request, key)
            gt = value > compare
            reasons.append({key: gt})
            if not gt:
                result = False
        return result, json.dumps(reasons, indent=4)


class LesserThanPolicy(Policy):
    def __init__(self, arguments: Dict[str, Any]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key, compare in self.arguments.items():
            value = hierarchical_dict_lookup(request.raw_request, key)
            lt = value < compare
            reasons.append({key: lt})
            if not lt:
                result = False
        return result, json.dumps(reasons, indent=4)


class GreaterThanEQPolicy(Policy):
    def __init__(self, arguments: Dict[str, Any]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key, compare in self.arguments.items():
            value = hierarchical_dict_lookup(request.raw_request, key)
            ge = value >= compare
            reasons.append({key: ge})
            if not ge:
                result = False
        return result, json.dumps(reasons, indent=4)


class LesserThanEQPolicy(Policy):
    def __init__(self, arguments: Dict[str, Any]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key, compare in self.arguments.items():
            value = hierarchical_dict_lookup(request.raw_request, key)
            le = value <= compare
            reasons.append({key: le})
            if not le:
                result = False
        return result, json.dumps(reasons, indent=4)


class MatchPolicy(Policy):
    def __init__(self, arguments: Dict[str, List[Any]]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key, allowable in self.arguments.items():
            value = hierarchical_dict_lookup(request.raw_request, key)
            is_allowed = value in allowable
            reasons.append({key: is_allowed})
            if not is_allowed:
                result = False
        return result, json.dumps(reasons, indent=4)


"""
A policy is an object that validates a request.
A policy is a collection of behaviors.

We can define policy P as:

P = {b1, b2, b3, b4, .... bn}
Where bi is some behavior that defines a type of validation.

A behavior may be one of these:
TODO 1. Match(key, [v1, v2, v3, ...., vn]) where vi is an allowable value for a key
2. Lesser_Than(key1, key2) is key1 < key2 DONE
3. Greater_Than(key1, key2) is key1 > key2 DONE
4. Lesser_ThanEQ(key1, key2) is key1 <= key2
5. Greater_ThanEQ(key1, key2) is key1 >= key2 
6. Equal(key1, key2) is key1 == key2 DONE
7. Format(ke1, f) where f is a format type element of Formats DONE
8. and(b1, b2, ....) where all behaviors bi apply DONE
9. Or(b1, b2, ....) where at least one behavior bi applies DONE
10. Required_Headers(h1, h2, .... hn) where hn is a required header DONE

Formats:
1. iso8601
"""


class PolicyFactory:
    @staticmethod
    def create_full_approval_policy() -> Policy:
        return Policy(full_approval=True)

    @staticmethod
    def get_cascade_policy_from_list(arg: List) -> Policy:
        return AndPolicy(arg)

    @staticmethod
    def get_policy_from_dict(arg: Dict, return_policy_list: bool = False) -> Union[CascadedPolicy | List[Policy]]:
        """
        :param arg:
        :param return_policy_list: If we should return the list of policies instead of the wrapped version.
        :return:
        """
        policy_lookup = {
            "required_headers": RequiredHeaderPolicy,
            "or": OrPolicy,
            "and": AndPolicy,
            "formatted_arguments": ArgumentFormatPolicy,
            "equality": EqualityPolicy,
            "greater_than": GreaterThanPolicy,
            "greater_than_eq": GreaterThanEQPolicy,
            "lesser_than": LesserThanPolicy,
            "lesser_than_eq": LesserThanEQPolicy,
            "match": MatchPolicy
        }

        policies = []
        for key, value in arg.items():
            policies.append(policy_lookup[key](value))
        return AndPolicy(policies) if not return_policy_list else policies

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


if __name__ == "__main__":
    import json

    policy_test = {
        "formatted_arguments": {
            "data.date": "iso8601",
            "data.date2": "iso8601"
        },
        "equality": ["data.date", "data.date2"],
        "lesser_than_eq": {
            "data.date": "2024-01-12T12:30:16.001Z"
        },
        "or": [
            {"match": {
                "hello": ["worlds", "world"]
            }},
            {"match": {
                "hello": ["wor2ld", "world"]
            }}
        ]
    }
    policy = PolicyFactory.get_policy_from_argument(policy_test)
    request_sample = {
        "header": "hi",
        "request": "uofc.hi",
        "data": {
            "date": "2024-01-12T12:30:16.001Z",
            "date2": "2024-01-12T12:30:16.001Z"
        },
        "hello": "wor2ld"
    }
    encoded_data = json.dumps(request_sample, indent=4).encode('utf-8')
    request = Request(encoded_data)
    result, reason = policy(request)
    print(reason)
    print(result)
