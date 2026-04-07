
from enum import Enum, StrEnum

class AudioReadable(StrEnum):
    READABLE = "readable"
    UNREADABLE = "unreadable_or_corrupt"
    
    @classmethod
    def get_value(cls, key: str) -> str:
        # Allows you to look up "high" and get "320k" safely
        return cls[key.upper()].value

    @classmethod
    def from_str(cls, label: str):
        """Safely find a tier by string, case-insensitive."""
        try:
            return cls[label.upper()]
        except (KeyError, AttributeError):
            return None  # Or return cls.MEDIUM as a safe fallback

