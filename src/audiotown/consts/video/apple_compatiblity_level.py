from enum import Enum, StrEnum

class AppleCompatibilityLevel(Enum):
    APPLE_SAFE = "apple_safe"
    GENERAL_SAFE = "general_safe"
    ARCHIVE = "archive"