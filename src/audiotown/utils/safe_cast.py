from typing import Callable, TypeVar, Any

# I don't know what this type is yet, but it will be the same type in multiple places."
T = TypeVar("T")


# target_type: Callable[[object], T]
# def safe_cast(value: object| None, target_type: Callable[[object], T]) -> T | None:
def safe_cast(value: Any, target_type: Callable[[Any], T]) -> T | None:

    """
        Safely convert a value into a specififc type dicated by `T`
        ratio = safe_cast("1.5", float)
    Args:
        value (object | None): _description_
        target_type (Callable[[object], T]): _description_

    Returns:
        T | None: _description_
    """
    if value in (None, ""):
        return None
    try:
        return target_type(value)
    except (TypeError, ValueError):
        return None