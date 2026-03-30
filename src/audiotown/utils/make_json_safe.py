from dataclasses import asdict
from pathlib import Path
from typing import Any
from datetime import datetime
from enum import Enum
from collections import Counter,defaultdict

def make_json_safe(value: Any) -> Any:
    """
    Recursively normalize a value into JSON-serializable data.

    Converts unsupported objects such as `Path` into JSON-friendly types and
    walks nested containers like dict, list, tuple, and set to clean their
    contents as well.

    Args:
        value: The value to normalize.

    Returns:
        A version of `value` that can be safely passed to `json.dumps()`.
    """
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Counter):
        return dict(value)
    if isinstance(value, defaultdict):
        return dict(value)
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [make_json_safe(v) for v in value]
    if isinstance(value, set):
        return [make_json_safe(v) for v in value]
    return value