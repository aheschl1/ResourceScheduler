from backend.gateway.client_connection import ClientConnection
from backend.utils.constants import *
import socket
from multiprocessing.pool import Pool
import numpy as np
from utils.constants import BUFFER_SIZE, DEFAULT_IP, DEFAULT_PORT


class TCPServer:
    buffer_size: int = BUFFER_SIZE

    def __init__(self,
                 ip: str = DEFAULT_IP,
                 port: int = DEFAULT_PORT,
                 protocol: str = TCP,
                 processes: int = 1
                 ):

        assert protocol == TCP, "TCP is only implemented protocol"
        self._protocol = protocol
        self._processes = processes
        self._ip = ip
        self._port = port
        self._sockets = self._instantiate_sockets()

    @staticmethod
    def _start_process(s: socket.socket) -> None:
        """
        Launched off main process with a socket
        :param s: socket to connect with
        :return: None
        """
        with s:
            s.listen()
            connection, address = s.accept()
            print(f"=====A process has connected to {address}=====")
            communicator = ClientConnection(connection, address, buffer_size=TCPServer.buffer_size)
            with connection:
                try:
                    communicator.start()
                except Exception as e:
                    connection.sendall(f"Server Error: {e}".encode())
                    print(f"Server Error: {e}")
            print(f"=====Process connected to {address} has ended=====")

    def start(self):
        """
        Wait for a connection, and then pass it off the ClientCommunications
        :return:
        """
        with Pool(self._processes) as pool:
            print(f"Starting {self._processes} server processes")
            pool.map(TCPServer._start_process, self._sockets)

    def _instantiate_sockets(self):
        """
        Creates a socket for each process
        :return: socket
        """
        if self._protocol == TCP:
            socket_type = socket.SOCK_STREAM
        else:
            raise NotImplementedError("Unsupported protocol")
        sockets = []
        for process in range(self._processes):
            _socket = socket.socket(socket.AF_INET, socket_type)
            _socket.bind((self._ip, self._port+process))
            sockets.append(_socket)
        return sockets


if __name__ == "__main__":
    server = TCPServer(processes=1)
    server.start()
