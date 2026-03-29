from enum import StrEnum
from dataclasses import dataclass, field
from pathlib import Path

class Action(StrEnum):
    REMUX = "Quick Move (Container Swap)"
    TRANSCODE = "Full Upgrade (Apple Ready)"
    REPAIR = "Repair Timestamps"
    SKIP = "Perfect / No Action"

@dataclass(slots=True)
class MediaReport:
    file_path: Path
    action: Action
    video_codec: str
    audio_codec: str
    is_apple_ready: bool
    description: str = ""