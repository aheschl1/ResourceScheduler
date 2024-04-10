from abc import abstractmethod
from typing import Tuple

from backend.requests.requests import Request


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
