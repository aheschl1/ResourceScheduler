import socket
from typing import Dict

from backend.gateway.response_formats import Response
from backend.requests.requests import Request
from backend.routing.root_authority import RootAuthority
from utils.constants import *
from utils.errors import ValidationError, RejectedRequestError, RoutingError, DatabaseWriteError, InvalidRequestError


class ClientConnection:
    def __init__(self, connection: socket.socket, address: str, buffer_size: int = 1024):
        self._socket = connection
        self._address = address
        self._buffer_size = buffer_size

    def _do_task(self):
        """
        Starts communicating with client
        :return:
        """
        data = self._socket.recv(self._buffer_size)
        print(f"Received {data.decode()}\nProcessing request")
        if not data:
            return
        request_parser = Request(data)
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
        except InvalidRequestError as invalid_request_error:
            response = Response(
                status_code=INVALID_REQUEST,
                error=str(invalid_request_error)
            )
            self._socket.sendall(response.get_bytes())
            return
        except DatabaseWriteError as database_write_error:
            # data provided couldn't be written
            response = Response(
                status_code=POOR_FORMAT,
                error=str(database_write_error)
            )
            self._socket.sendall(response.get_bytes())
            return
        except Exception as exception:
            response = Response(
                status_code=UNKNOWN,
                error=str(exception)
            )
            self._socket.sendall(response.get_bytes())
            return

    def start(self):
        self._do_task()
        self._socket.close()
        print(f"=====Process connected to {self._address} is done=====")

    def __del__(self):
        try:
            self._socket.close()
        except Exception:
            ...
