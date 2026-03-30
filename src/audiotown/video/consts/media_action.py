from enum import StrEnum

class MediaAction(StrEnum):
    REMUX = "Quick Move (Container Swap)"
    TRANSCODE = "Full Upgrade (Apple Ready)"
    REPAIR = "Repair Timestamps"
    SKIP = "Perfect / No Action"
