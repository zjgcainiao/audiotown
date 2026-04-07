from typing import Callable, TypeVar

T = TypeVar("T")

def safe_cast(value: object, target_type: Callable[[object], T]) -> T | None:
    if value in (None, ""):
        return None
    try:
        return target_type(value)
    except (TypeError, ValueError):
        return None