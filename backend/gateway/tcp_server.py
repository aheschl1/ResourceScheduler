import sys
sys.path.append("/home/andrewheschl/PycharmProjects/ResourceScheduler")
from multiprocessing import Process

from backend.gateway.client_connection import ClientConnection
from backend.utils.constants import *
import socket
from utils.constants import BUFFER_SIZE, DEFAULT_IP, DEFAULT_PORT


class TCPServer:
    buffer_size: int = BUFFER_SIZE

    def __init__(self,
                 ip: str = DEFAULT_IP,
                 port: int = DEFAULT_PORT,
                 protocol: str = TCP,
                 timeout: int = 2
                 ):

        assert protocol == TCP, "TCP is only implemented protocol"
        self._protocol = protocol
        self._ip = ip
        self._port = port
        self._socket = self._instantiate_socket()
        self._timeout = timeout
        self._kill = False

    def start(self) -> None:
        """
        Launches client connection off main process with a socket
        :return: None
        """
        with self._socket:
            self._socket.listen()  # syn request
            self._socket.settimeout(self._timeout)
            while not self._kill:
                try:
                    connection, address = self._socket.accept()
                except TimeoutError: continue

                print(f"=====A process has connected to {address}=====")
                communicator = ClientConnection(connection, address, buffer_size=TCPServer.buffer_size)
                try:
                    communicator_process = Process(
                        target=communicator.start
                    )
                    communicator_process.start()
                except Exception as e:
                    connection.sendall(f"Server Error: {e}".encode())
                    print(f"Server Error: {e}")
                print(f"=====Process connected to {address} has ended=====")
        print("Server terminated")

    def _instantiate_socket(self):
        """
        Creates a socket for each process
        :return: socket
        """
        if self._protocol == TCP:
            socket_type = socket.SOCK_STREAM
        else:
            raise NotImplementedError("Unsupported protocol")
        _socket = socket.socket(socket.AF_INET, socket_type)
        _socket.bind((self._ip, self._port))
        return _socket

    def kill(self):
        self._kill = True


if __name__ == "__main__":
    server = TCPServer()
    server.start()
