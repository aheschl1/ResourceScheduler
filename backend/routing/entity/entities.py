from typing import Union, Dict, List

from backend.requests.request_validation import RequestParser, BottomOfRequestError
from backend.routing.entity.policy import Policy
from utils.errors import RoutingError, RejectedRequestError


class Entity:
    def __init__(self, name: str, policy: Policy, children: List):
        self._children = {child.name:child for child in children}
        self._policy = policy
        self._name = name

    def __call__(self, request: RequestParser) -> Dict:
        """
        Children should actually do something, and then call super to move on
        :param request:
        :return:
        """
        assert self._children is not None, "Entity not fully initialized, set children"
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

    @property
    def name(self):
        return self._name


class RoutingEntity(Entity):
    def __init__(self, name, policy, children):
        super().__init__(name, policy, children)

    def handle_bottom_of_tree(self, request: RequestParser) -> Dict:
        raise RoutingError(f"{self.name} is a routing entity, and should not be a leaf")

    def validate_request(self, request: RequestParser) -> Union[bool, str]:
        # TODO probably use the policy
        return True


class SlottedEntity(Entity):
    def __init__(self, name, policy, children):
        super().__init__(name, policy, children)

    def _manage_slot_request(self, request: RequestParser) -> Dict:
        # TODO do stuff
        ...

    def handle_bottom_of_tree(self, request: RequestParser) -> Dict:
        result = self._manage_slot_request(request)
        return result

    def validate_request(self, request: RequestParser) -> Union[bool, str]:
        # TODO probably use the policy
        return True


class TicketedEntity(Entity):
    def __init__(self, name, policy, children):
        super().__init__(name, policy, children)

    def _manage_ticket_request(self, request: RequestParser) -> Dict:
        # TODO do stuff
        ...

    def handle_bottom_of_tree(self, request: RequestParser) -> Dict:
        result = self._manage_ticket_request(request)
        return result

    def validate_request(self, request: RequestParser) -> Union[bool, str]:
        # TODO probably use the policy
        return True


def get_entity_class_from_type_string(type_string: str) -> Entity:
    mapping = {
        "Routing": RoutingEntity,
        "Slotted": SlottedEntity,
        "Ticketed": TicketedEntity
    }
    return mapping[type_string]
