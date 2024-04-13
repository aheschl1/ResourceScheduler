import json
import re
from typing import List, Tuple, Dict, Any

from backend.policies.policy import Policy
from backend.requests.requests import Request
from backend.utils.utils import hierarchical_dict_lookup


class EqualityPolicy(Policy):
    """
    Policy to check if request[key1] == request[key2] == request[key3] ... == request[keyn]
    """

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


class MatchPolicy(Policy):
    """
    Policy to check if request[key1] == val1 or request[key1] == val2 or ... or request[key1] == valn
    """

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


class RegularExpressionPolicy(Policy):
    """
    Matches a value against a regular expression.
    """
    def __init__(self, arguments: Dict[str, str]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key, expression in self.arguments.items():
            value = hierarchical_dict_lookup(request.raw_request, key)
            try:
                match = re.search(expression, value) is not None
            except re.error:
                match = False
            reasons.append({key: match})
            if not match:
                result = False
        return result, json.dumps(reasons, indent=4)
