import http.client

from utils.constants import DEFAULT_IP, DEFAULT_PORT, BUFFER_SIZE


class HTTPClient:
    def __init__(self, ip: str = DEFAULT_IP, port: int = DEFAULT_PORT, buffer_size: int = BUFFER_SIZE):
        self._ip = ip
        self._port = port
        self._buffer_size = buffer_size
        self._socket: http.client.HTTPConnection = http.client.HTTPConnection(DEFAULT_IP, DEFAULT_PORT)

    def start(self):
        with open("/home/andrewheschl/PycharmProjects/ResourceScheduler/client/samples/andrew_request") as f:
            to_send = f.read()
        self._socket.request("POST", "/", body=to_send)
        data = self._socket.getresponse()
        print(data.read().decode())
        self._socket.close()

    def __del__(self):
        self._socket.close()


if __name__ == "__main__":
    client = HTTPClient(port=DEFAULT_PORT)
    client.start()
