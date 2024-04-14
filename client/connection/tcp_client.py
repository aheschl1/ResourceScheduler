import socket

from utils.constants import DEFAULT_IP, DEFAULT_PORT, BUFFER_SIZE


class TCPClient:
    def __init__(self, ip: str = DEFAULT_IP, port: int = DEFAULT_PORT, buffer_size: int = BUFFER_SIZE):
        self._ip = ip
        self._port = port
        self._buffer_size = buffer_size
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        with open("/home/andrewheschl/PycharmProjects/ResourceScheduler/client/samples/empty_request") as f:
            to_send = f.read()
            
        with self._socket as s:
            print(self._ip, self._port)
            s.connect((self._ip, self._port))
            s.sendall(to_send.encode())
            data = s.recv(self._buffer_size)
            print(data.decode())

    def __del__(self):
        self._socket.close()


if __name__ == "__main__":
    client = TCPClient(port=DEFAULT_PORT)
    client.start()
