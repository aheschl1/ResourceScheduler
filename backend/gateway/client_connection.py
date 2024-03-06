import socket
from typing import Dict

from backend.gateway.request_decoding import decode_request
from backend.gateway.response_formats import Response
from backend.requests.request_validation import RequestParser
from backend.router.root_authority import RootAuthority
from utils.constants import POOR_FORMAT
from utils.errors import ValidationError


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
        while True:
            data = self._socket.recv(self._buffer_size)
            print(f"Received {len(data)} bytes from {self._address}")
            if not data:
                break
            request_parser = RequestParser(data)
            try:
                # check if request is even valid
                request_parser.validate()
            except ValidationError as e:
                # invalid request
                response = Response(status_code=POOR_FORMAT, error=str(e))
                self._socket.sendall(response.get_bytes())

            root_authority = RootAuthority(request_parser)
            root = root_authority.get_root()
