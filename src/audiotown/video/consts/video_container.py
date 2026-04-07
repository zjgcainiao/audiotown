from __future__ import annotations
from enum import Enum


class VideoContainer(Enum):
    MP4 = (".mp4", "mp4", "MPEG-4 Part 14")
    MKV = (".mkv", "matroska", "Matroska")
    AVI = (".avi", "avi", "Audio Video Interleave")
    MOV = (".mov", "mov", "QuickTime / MOV")
    WEBM = (".webm", "webm", "WebM")
    RMVB = (".rmvb", "rm", "RealMedia Variable Bitrate")
    RM = (".rm", "rm", "RealMedia")

    def __init__(self, suffix: str, muxer: str, description: str):
        self.suffix = suffix
        self.muxer = muxer
        self.description = description

    @classmethod
    def from_format_name(cls, format_name: str | None) -> VideoContainer | None:
        """Map ffprobe format_name to a normalized VideoContainer."""
        if format_name is None:
            return None
        # ffprobe returned `"mov, mp4, m4a, 3gp, 3g2, mj2"`
        format_names = {
            part.strip().lower() for part in format_name.split(",") if part.strip()
        }
        for member in cls:
            if member.muxer in format_names:
                return member
        return None

    @classmethod
    def from_suffix(cls, suffix: str | None) -> VideoContainer | None:
        """Map ffprobe suffix to a normalized VideoContainer."""
        if suffix is None:
            return None
        suffix = suffix.lower().strip()
        for member in cls:
            if member.suffix in suffix:
                return member
        return None
