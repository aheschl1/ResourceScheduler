from backend.requests.request_validation import RequestParser


class RootAuthority:
    def __init__(self, request: RequestParser):
        self._request = request

    def get_root(self):
        """
        Should return an object which can start routing the request
        This should be the head of a tree...
        #TODO do it
        :return:
        """
        ...
