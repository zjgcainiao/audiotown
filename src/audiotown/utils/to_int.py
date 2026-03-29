def to_int(val, default=0) -> int:
    """Safely converts a value to integer, returning default on failure."""
    try:
        # We strip() in case there are hidden spaces like " 2024 "
        return int(str(val).strip())
    except (ValueError, TypeError):
        return default
