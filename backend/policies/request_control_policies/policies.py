import json
from typing import Dict, Tuple

from backend.policies.policy import Policy
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
    """
    Policy to ensure that request[keyi] is policyi
    """
    def __init__(self, requirements: Dict[str, str]):
        super().__init__(False)
        self.requirements = requirements
        self._formats = {
            "iso8601": validate_iso8601
        }

    def validate(self, request: Request) -> Tuple[bool, str]:
        result, reasons = True, []
        for key, format_check in self.requirements.items():
            value = hierarchical_dict_lookup(request.raw_request, key)
            try:
                validator = self._formats[format_check]
            except KeyError:
                return False, f"Unknown/Unimplemented format '{format_check}'"
            in_format = validator(value)
            reasons.append({f"{key}": in_format})
            if not in_format:
                result = False

        return result, json.dumps(reasons, indent=4)
