from abc import abstractmethod
from typing import Tuple

from backend.requests.requests import Request


class Behavior:
    def __init__(self, id: int, *args, **kwargs):
        self.id = id

    @abstractmethod
    def __call__(self, request: Request, **kwargs) -> Tuple[bool, str]:
        return True, "allowed"


class LesserThan(Behavior):
    def __init__(self, id: int, *args, **kwargs):
        super().__init__(id, *args, **kwargs)

    def __call__(self, request: Request, **kwargs) -> Tuple[bool, str]:
        return True, "allowed"
