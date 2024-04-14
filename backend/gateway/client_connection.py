import json
import socket
from typing import Dict

from backend.database_endpoints.data_management import DataQueryManagement
from backend.database_endpoints.entity_creation import EntityEntryDataManagement
from backend.gateway.response_formats import Response
from backend.requests.requests import Request
from backend.routing.root_authority import RootAuthority
from utils.constants import *
from utils.errors import ValidationError, RejectedRequestError, RoutingError, DatabaseWriteError, InvalidRequestError
import traceback


class ClientConnection:
    def __init__(self, connection: socket.socket, address: str, buffer_size: int = 1024):
        """
        This class handles a single instance of a client request off the main server process.
        If this ends up being run on the main process, get ready to die.
        :param connection:
        :param address:
        :param buffer_size:
        """
        self._socket = connection
        self._address = address
        self._buffer_size = buffer_size

    def _post(self, request: Request) -> Response:
        """
        Handles the post request (registers resources)
        :param request:
        :return:
        """
        try:
            # check if request is even valid
            request.validate()
        except ValidationError as e:
            # invalid request
            return Response(status_code=POOR_FORMAT, error=str(e))

        root_authority = RootAuthority(request)
        try:
            # find root node
            root = root_authority.get_root()
            # get result (maybe)
            result = root(request)
            # success !!
            return Response(status_code=SUCCESS, data=result)
        except RejectedRequestError as rejection:
            # One of the entities said no
            return Response(
                status_code=REJECTED_BY_ENTITY,
                error=str(rejection)
            )
        except RoutingError as routing_error:
            # The path specified lead to a dead-end
            return Response(
                status_code=ROUTE_DNE,
                error=str(routing_error)
            )
        except InvalidRequestError as invalid_request_error:
            return Response(
                status_code=INVALID_REQUEST,
                error=str(invalid_request_error)
            )
        except DatabaseWriteError as database_write_error:
            # data provided couldn't be written
            return Response(
                status_code=POOR_FORMAT,
                error=str(database_write_error)
            )
        except Exception as exception:
            return Response(
                status_code=UNKNOWN,
                error=str(exception)
            )

    def _put(self, request: Request) -> Response:
        """
        Request to create a new entity
        :param request:
        :return:
        """
        try:
            EntityEntryDataManagement(request).build_new()
            # success !!
            return Response(status_code=SUCCESS, data="Your association, entities, and relevant data tables have been created!")
        except Exception as e:
            return Response(
                status_code=POOR_FORMAT,
                error=str(e)
            )

    def _get(self, request: Request) -> Response:
        """
        Method for getting data related to an entity.
        :param request:
        :return:
        """
        try:
            request.validate()
            result = DataQueryManagement(request).query()
            # success !!
            return Response(status_code=SUCCESS, data=json.dumps(result, indent=4))
        except Exception as e:
            return Response(
                status_code=POOR_FORMAT,
                error=str(e)
            )

    def _do_task(self) -> Response:
        """
        Starts communicating with client
        :return:
        """
        data = self._socket.recv(self._buffer_size)
        print(f"Received {data.decode()}\nProcessing request")
        request_parser = Request(data)
        method = request_parser.request_method
        if method == "POST":
            return self._post(request_parser)
        elif method == "PUT":
            return self._put(request_parser)
        elif method == "GET":
            return self._get(request_parser)
        else:
            raise NotImplementedError(f"Requested method {method} is not yet implemented :(")

    def start(self):
        try:
            response = self._do_task()
        except Exception as e:
            response = Response(500, error=f"Server Error: {e}")
            print(f"Server Error: {e}")
        print(f"Response:\n{response.get_bytes().decode()}")
        print(f"Errors: {traceback.format_exc()}")
        self._socket.sendall(response.get_bytes())
        self._socket.close()
        print(f"=====Process connected to {self._address} is closed=====")

    def __del__(self):
        try:
            self._socket.close()
        except Exception:
            ...
