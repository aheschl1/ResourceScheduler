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
