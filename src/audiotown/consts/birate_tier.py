
from enum import Enum, StrEnum

class BitrateTier(str, Enum):
    HIGH = "320k"
    MEDIUM = "256k"
    LOW = "128k"

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

    @classmethod
    def supported_bitrates(cls) -> set[str]:
        # Allows you to look up "high" and get "320k" safely

        a_set = {member.value for member in cls}
        return a_set
