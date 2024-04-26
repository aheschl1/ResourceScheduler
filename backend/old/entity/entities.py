from abc import abstractmethod
from typing import Union, Dict, List, Tuple, Any

from backend.database_endpoints.data_management import TicketDataManagement, TimeslotDataManagement, DataQueryManagement
from backend.requests.requests import Request, BottomOfRequestError
from backend.policies.policy import Policy
from utils.errors import RoutingError, RejectedRequestError, InvalidRequestError


class Entity:
    def __init__(self, name: str, policy: Policy, children: List, org_name: str):
        self._children = {child.name: child for child in children}
        self._policy = policy
        self._name = name
        self._org_name = org_name

    def get_children_of(self, path: str, recursive: bool) -> List:
        """
        Returns the entity object at and below the given path.
        :param recursive: If we should be recursive, or just find the exact node
        :param path: The path to search at.
        :return: List of entities
        """
        paths = path.split(".")
        if self._name != paths[0]:
            raise RoutingError(f"Tried to get entity children, but {path} doesn't exist on {self._name}'s tree.")
        results = []
        if len(paths) == 1:
            # Meaning we are the lookup node!
            results.append(self)
            if recursive:
                for name, entity in self._children.items():
                    results.extend(entity.get_children_of(name, recursive))
            return results
        else:
            # traverse to find the target
            return self._children[paths[1]].get_children_of('.'.join(paths[1:]), recursive)

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

    @abstractmethod
    def query_data(self, filters: Any = None) -> Tuple[Dict, Dict]: ...

    @abstractmethod
    def handle_bottom_of_tree(self, request: Request) -> Dict:
        raise NotImplementedError("Create entity subclass")

    @abstractmethod
    def validate_request(self, request: Request) -> Union[bool, str]:
        raise NotImplementedError("Create entity subclass")

    @property
    def name(self):
        return self._name

    @property
    def policy(self):
        return self._policy

    @property
    def org_name(self):
        return self._org_name


class RoutingEntity(Entity):
    def __init__(self, name, policy, children, org_name):
        super().__init__(name, policy, children, org_name)

    def query_data(self, filters: Any = None) -> Tuple[Dict, Dict]:
        raise InvalidRequestError("Cannot query data from a routing entity :`(")

    def handle_bottom_of_tree(self, request: Request) -> Dict:
        raise RoutingError(f"{self.name} is a routing entity, and should not be a leaf")

    def validate_request(self, request: Request) -> Tuple[bool, str]:
        return self.policy.validate(request)


class SlottedEntity(Entity):
    def __init__(self, name, policy, children, org_name):
        super().__init__(name, policy, children, org_name)

    def query_data(self, filters: Any = None) -> Tuple[Dict, Dict]:
        return DataQueryManagement.read_data_from_entity_and_organization_name(self.org_name, self.name)

    @staticmethod
    def _manage_slot_request(request: Request) -> Dict:
        database_manager = TimeslotDataManagement(request.root_name, request.current_name)
        database_manager.register(request.raw_request)

        return {
            "result": "ok"
        }

    def handle_bottom_of_tree(self, request: Request) -> Dict:
        result = self._manage_slot_request(request)
        return result

    def validate_request(self, request: Request) -> Tuple[bool, str]:
        return self.policy.validate(request)


class TicketedEntity(Entity):
    def __init__(self, name, policy, children, org_name):
        super().__init__(name, policy, children, org_name)

    def query_data(self, filters: Any = None) -> Tuple[Dict, Dict]:
        return DataQueryManagement.read_data_from_entity_and_organization_name(self.org_name, self.name)

    @staticmethod
    def _manage_ticket_request(request: Request) -> Dict:
        database_manager = TicketDataManagement(request.root_name, request.current_name)
        database_manager.register(data=request.raw_request)

        return {
            "result": "ok"
        }

    def handle_bottom_of_tree(self, request: Request) -> Dict:
        result = TicketedEntity._manage_ticket_request(request)
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
