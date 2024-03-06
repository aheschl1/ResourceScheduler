import socket
from typing import Dict

from backend.gateway.response_formats import Response
from backend.requests.request_validation import RequestParser
from backend.routing.root_authority import RootAuthority
from utils.constants import *
from utils.errors import ValidationError, RejectedRequestError, RoutingError


class ClientConnection:
    def __init__(self, connection: socket.socket, address: str, buffer_size: int = 1024):
        self._socket = connection
        self._address = address
        self._buffer_size = buffer_size

    def start(self):
        """
        Starts communicating with client
        :return:
        """
        data = self._socket.recv(self._buffer_size)
        print(f"Received {data.decode()}\nProcessing request")
        if not data:
            return
        request_parser = RequestParser(data)
        try:
            # check if request is even valid
            request_parser.validate()
        except ValidationError as e:
            # invalid request
            response = Response(status_code=POOR_FORMAT, error=str(e))
            self._socket.sendall(response.get_bytes())
            return

        root_authority = RootAuthority(request_parser)
        try:
            # find root node
            root = root_authority.get_root()
            # get result (maybe)
            result = root(request_parser)
            # success !!
            response = Response(status_code=SUCCESS, data=result)
            self._socket.sendall(response.get_bytes())
        except RejectedRequestError as rejection:
            # One of the entities said no
            response = Response(
                status_code=REJECTED_BY_ENTITY,
                error=str(rejection)
            )
            self._socket.sendall(response.get_bytes())
            return
        except RoutingError as routing_error:
            # The path specified lead to a dead-end
            response = Response(
                status_code=ROUTE_DNE,
                error=str(routing_error)
            )
            self._socket.sendall(response.get_bytes())
            return

    def __del__(self):
        self._socket.close()

