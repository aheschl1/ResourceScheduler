import socket
from typing import Dict

from backend.gateway.request_decoding import decode_request
from backend.gateway.response_formats import Response
from backend.requests.request_validation import RequestParser
from utils.constants import POOR_FORMAT
from utils.errors import ValidationError


class ClientConnection:
    def __init__(self, connection: socket.socket, address: str, buffer_size: int = 1024):
        self._socket = connection
        self._address = address
        self._buffer_size = buffer_size

    def start(self):
        while True:
            data = self._socket.recv(self._buffer_size)
            print(f"Received {len(data)} bytes from {self._address}")
            if not data:
                break
            request_parser = RequestParser(data)
            try:
                request_parser.validate()
            except ValidationError as e:
                response = Response(status_code=POOR_FORMAT, error=str(e))
                self._socket.sendall(response.get_bytes())

