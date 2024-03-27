
"""
A policy is an object that validates a request.
A policy is a collection of behaviors.

We can define policy P as:

P = {b1, b2, b3, b4, .... bn}
Where bi is some behavior that defines a type of validation.

A behavior may be one of these:
1. Match(key, [v1, v2, v3, ...., vn]) where vi is an allowable value for a key
2. Lesser_Than(key1, key2) is key1 < key2
3. Greater_Than(key1, key2) is key1 > key2
4. Lesser_ThanEQ(key1, key2) is key1 <= key2
5. Greater_ThanEQ(key1, key2) is key1 >= key2
6. Equal(key1, key2) is key1 == key2
7. Format(ke1, f) where f is a format type element of Formats
8. and(b1, b2, ....) where all behaviors bi apply
9. Or(b1, b2, ....) where at least one behavior bi applies

Formats:
1. iso8601
"""
from typing import List, Callable


class Policy:
    def __init__(self, id: int, behavior_ids: List[int]):
        self._id = id
        self._behavior_ids = behavior_ids
        self._behaviors: List[Callable] = self._build_behaviors()

    def _build_behaviors(self) -> List[Callable]:
        behaviors = []
        for behavior_id in self._behavior_ids:
            behaviors.append()