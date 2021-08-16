from dataclasses import dataclass
from typing import Any

from typing import TypeVar, Generic

T = TypeVar('T')


@dataclass()
class G3Result(Generic[T]):
    retco: int = 0
    result: T = None

