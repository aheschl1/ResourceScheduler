class ValidationError(Exception):
    def __init__(self, message: str = ""):
        self._message = message

    def __str__(self):
        return f"ValidationError: {self._message}"


class InternalResponseError(Exception):
    def __init__(self, message: str = ""):
        self._message = message

    def __str__(self):
        return f"InternalResponseError: {self._message}"


class RoutingError(Exception):
    def __init__(self, message: str = ""):
        self._message = message

    def __str__(self):
        return f"RoutingError: {self._message}"


class BottomOfRequestError(Exception):
    def __str__(self):
        return f'BottomOfRequestError'


class RejectedRequestError(Exception):
    def __init__(self, message: str = ""):
        self._message = message

    def __str__(self):
        return f'RejectedRequestError: {self._message}'


class NoTicketsAvailableError(Exception):
    def __init__(self, message: str = ""):
        self._message = message

    def __str__(self):
        return f'NoTicketsAvailableError: {self._message}'


class DatabaseWriteError(Exception):
    def __init__(self, message: str = ""):
        self._message = message

    def __str__(self):
        return f'DatabaseWriteError: {self._message}'


class InvalidRequestError(Exception):
    def __init__(self, message: str = ""):
        self._message = message

    def __str__(self):
        return f'InvalidDataRequest: {self._message}'
