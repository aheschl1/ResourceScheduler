from typing import Union, Dict, List, Tuple

from backend.requests.requests import Request, BottomOfRequestError
from backend.routing.entity.policy import Policy
from utils.errors import RoutingError, RejectedRequestError


class Entity:
    def __init__(self, name: str, policy: Policy, children: List):
        self._children = {child.name: child for child in children}
        self._policy = policy
        self._name = name

    def __call__(self, request: Request) -> Dict:
        """
        Children should actually do something, and then call super to move on

        Currently, we take no action unless at the bottom of the tree...
        It works as follows:
        -Validate with validate_request at current node
        -Try to extract next node
            - Success: recurse on next node
            - Failure: Bottom of tree, call handle_bottom_of_tree at current node and return result
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

    def handle_bottom_of_tree(self, request: Request) -> Dict:
        raise NotImplementedError("Create entity subclass")

    def validate_request(self, request: Request) -> Union[bool, str]:
        raise NotImplementedError("Create entity subclass")

    @property
    def name(self):
        return self._name

    @property
    def policy(self):
        return self._policy


class RoutingEntity(Entity):
    def __init__(self, name, policy, children):
        super().__init__(name, policy, children)

    def handle_bottom_of_tree(self, request: Request) -> Dict:
        raise RoutingError(f"{self.name} is a routing entity, and should not be a leaf")

    def validate_request(self, request: Request) -> Tuple[bool, str]:
        return self.policy.validate(request)


class SlottedEntity(Entity):
    def __init__(self, name, policy, children):
        super().__init__(name, policy, children)

    def _manage_slot_request(self, request: Request) -> Dict:
        # TODO do stuff
        return {
            "result": "ok"
        }

    def handle_bottom_of_tree(self, request: Request) -> Dict:
        result = self._manage_slot_request(request)
        return result

    def validate_request(self, request: Request) -> Tuple[bool, str]:
        return self.policy.validate(request)


class TicketedEntity(Entity):
    def __init__(self, name, policy, children):
        super().__init__(name, policy, children)

    def _manage_ticket_request(self, request: Request) -> Dict:
        # TODO do stuff
        return {
            "result": "ok"
        }

    def handle_bottom_of_tree(self, request: Request) -> Dict:
        result = self._manage_ticket_request(request)
        return result

    def validate_request(self, request: Request) -> Tuple[bool, str]:
        return self.policy.validate(request)


def get_entity_class_from_type_string(type_string: str) -> Entity:
    mapping = {
        "Routing": RoutingEntity,
        "Slotted": SlottedEntity,
        "Ticketed": TicketedEntity
    }
    return mapping[type_string]
