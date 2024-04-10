import json
from typing import Dict, Any, Tuple

from backend.json_policies.policy import Policy
from backend.requests.requests import Request
from backend.utils.utils import hierarchical_dict_lookup


class GreaterThanPolicy(Policy):
    """
    Policy to check if request[key] > value
    """
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
    """
    Policy to check if request[key] < value
    """
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
    """
    Policy to check if request[key] >= value
    """
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
    """
    Policy to check if request[key] <= value
    """
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


class GreaterThanPolicyK(Policy):
    """
    Policy to check if request[key] > request[key2]
    """
    def __init__(self, arguments: Dict[str, Any]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key1, key2 in self.arguments.items():
            value1 = hierarchical_dict_lookup(request.raw_request, key1)
            value2 = hierarchical_dict_lookup(request.raw_request, key2)
            gt = value1 > value2
            reasons.append({key1: gt})
            if not gt:
                result = False
        return result, json.dumps(reasons, indent=4)


class LesserThanPolicyK(Policy):
    """
    Policy to check if request[key] < request[key2]
    """
    def __init__(self, arguments: Dict[str, Any]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key1, key2 in self.arguments.items():
            value1 = hierarchical_dict_lookup(request.raw_request, key1)
            value2 = hierarchical_dict_lookup(request.raw_request, key2)
            lt = value1 < value2
            reasons.append({key1: lt})
            if not lt:
                result = False
        return result, json.dumps(reasons, indent=4)


class GreaterThanEQPolicyK(Policy):
    """
    Policy to check if request[key] >= request[key2]
    """
    def __init__(self, arguments: Dict[str, str]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key1, key2 in self.arguments.items():
            value1 = hierarchical_dict_lookup(request.raw_request, key1)
            value2 = hierarchical_dict_lookup(request.raw_request, key2)
            ge = value1 >= value2
            reasons.append({key1: ge})
            if not ge:
                result = False
        return result, json.dumps(reasons, indent=4)


class LesserThanEQPolicyK(Policy):
    """
    Policy to check if request[key] <= request[key2]
    """
    def __init__(self, arguments: Dict[str, str]):
        super().__init__(False)
        self.arguments = arguments

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key1, key2 in self.arguments.items():
            value1 = hierarchical_dict_lookup(request.raw_request, key1)
            value2 = hierarchical_dict_lookup(request.raw_request, key2)
            le = value1 <= value2
            reasons.append({key1: le})
            if not le:
                result = False
        return result, json.dumps(reasons, indent=4)
