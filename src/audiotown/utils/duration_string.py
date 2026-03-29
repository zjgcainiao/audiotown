
def duration_string(duration: float) -> str:
    """genrate a human friendly format based on duration in seconds.
        Output will look like 20 mins, 30.5 hours, 30.0 days  or 1.2 years
    Args:
        duration (float): duration in seconds

    Returns:
        str: the human friendly string format
    """
    SECS_PER_HOUR = 60 * 60
    SECS_PER_DAY = 24 * SECS_PER_HOUR

    if duration <= 0:
        return ""
    elif duration < SECS_PER_HOUR:
        string = f"{duration/ SECS_PER_HOUR:,.1f} mins"
    elif duration < 100 * SECS_PER_HOUR:
        string = f"{duration/ SECS_PER_HOUR:,.1f} hours"
    elif duration < 400 * SECS_PER_DAY:
        string = f"{duration/ SECS_PER_DAY:,.1f} days"
    else:
        string = f"{duration/ SECS_PER_DAY:,.1f} years"
    return string

