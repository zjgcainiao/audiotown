
from typing import Optional

from datetime import datetime

def extract_year_from_str(value: str) -> Optional[int]:
    """
    Try to extract a 4-digit year from various messy formats.
    Returns None if no valid year found or out of reasonable range.
    """
    if not value or not isinstance(value, str):
        return None

    current_year = datetime.now().year

    # Try common patterns
    for fmt in [
        "%Y", "%y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%Y.%m.%d", "%d.%m.%Y", "%Y %m %d", "%b %d, %Y"
    ]:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            year = dt.year
            if 1900 <= year <= current_year + 5:
                return year
        except ValueError:
            continue

    # Fallback: look for any 4 consecutive digits in the string
    import re
    match = re.search(r'\b(19\d{2}|20\d{2})\b', value)
    if match:
        year = int(match.group(1))
        if 1900 <= year <= current_year + 5:
            return year

    return None
