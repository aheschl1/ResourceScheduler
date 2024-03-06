from typing import Union, Dict

from backend.requests.request_validation import RequestParser, BottomOfRequestError
from backend.routing.entity.policy import Policy
from utils.errors import RoutingError, RejectedRequestError


class Entity:
    def __init__(self, name: str, policy: Policy):
        self._children = {}
        self._policy = policy
        self._name = name

    def __call__(self, request: RequestParser) -> Dict:
        """
        Children should actually do something, and then call super to move on
        :param request:
        :return:
        """
        # Validate
        validated, reason = self.validate_request(request)
        if not validated:
            raise RejectedRequestError(f"{reason}")
        # Next route
        try:
            next_route_name = request.extract_next_route()
        except BottomOfRequestError:
            # Tree leaf
            return self.handle_bottom_of_tree(request)

        # Pass request forward
        if next_route_name not in self._children:
            raise RoutingError(f"No route named {next_route_name} in the children of {self._name}")

        return self._children[next_route_name](request)

    def handle_bottom_of_tree(self, request: RequestParser) -> Dict:
        raise NotImplementedError("Create entity subclass")

    def validate_request(self, request: RequestParser) -> Union[bool, str]:
        raise NotImplementedError("Create entity subclass")
