import json
from typing import Dict, Tuple

from backend.json_policies.policy import Policy
from backend.requests.requests import Request
from backend.utils.utils import hierarchical_dict_lookup, validate_iso8601


class RequiredHeaderPolicy(Policy):
    """
    Policy that checks whether all header exist.
    With strict mode, we can also enforce only these headers exist
    """
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
        result, reasons = True, []
        for header in self.required_headers:
            # asked for say data.quantity to exist
            try:
                hierarchical_dict_lookup(request.raw_request, header)
            except KeyError:
                result = False
                reasons.append({header: "missing"})
                continue

        if self.strict:
            for header in request.headers:
                if header not in self.required_headers:
                    result = False
                    reasons.append({header: "not allowed"})

        return result, json.dumps(reasons, indent=4)


class ArgumentFormatPolicy(Policy):
    """
    Policy to ensure that request[keyi] is policyi
    """
    def __init__(self, requirements: Dict[str, str]):
        super().__init__(False)
        self.requirements = requirements
        self._formats = {
            "iso8601": validate_iso8601,
            "dict": lambda x: isinstance(x, dict),
            "str": lambda x: isinstance(x, str),
            "int": lambda x: isinstance(x, int),
            "float": lambda x: isinstance(x, float)
        }

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key, format_check in self.requirements.items():
            try:
                value = hierarchical_dict_lookup(request.raw_request, key)
            except KeyError:
                result = False
                reasons.append({key: "missing"})
                continue

            try:
                validator = self._formats[format_check]
            except KeyError:
                result = False
                reasons.append({key: f"Unknown/Unimplemented format '{format_check}'"})
                continue
            in_format = validator(value)
            reasons.append({f"{key}": in_format})
            if not in_format:
                result = False

        return result, json.dumps(reasons, indent=4)
