from enum import StrEnum
from dataclasses import dataclass, field
from pathlib import Path
from .media_action import MediaAction

@dataclass(slots=True)
class MediaReport:
    file_path: Path
    action: MediaAction
    video_codec: str
    audio_codec: str
    is_apple_ready: bool
    description: str = ""