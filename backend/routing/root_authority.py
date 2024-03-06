from backend.requests.request_validation import RequestParser
from backend.routing.entity.entities import Entity


class RootAuthority:
    def __init__(self, request: RequestParser):
        self._request = request
        self._root_name = request.extract_next_route()

    def get_root(self) -> Entity:
        """
        Should return an object which can start routing the request
        This should be the head of a tree...
        #TODO do it
        :return:
        """
        # probably do something with _root_name ........
        ...
