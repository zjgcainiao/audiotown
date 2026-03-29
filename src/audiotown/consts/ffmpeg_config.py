
import shutil
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class FFmpegConfig:
    """
    Frozen configuration for FFmpeg and ffprobe executables.
    Defaults to system PATH lookup via shutil.which().
    """

    ffmpeg_path: Optional[str] = field(default_factory=lambda: shutil.which("ffmpeg"))
    ffprobe_path: Optional[str] = field(default_factory=lambda: shutil.which("ffprobe"))

    def __post_init__(self):
        # Optional: warn or raise if paths are missing (uncomment if desired)
        # if self.ffmpeg_path is None:
        #     raise ValueError("ffmpeg not found in PATH")
        # if self.ffprobe_path is None:
        #     raise ValueError("ffprobe not found in PATH")
        pass

    @property
    def is_complete(self) -> bool:
        """True if both executables were found."""
        return self.ffmpeg_path is not None and self.ffprobe_path is not None

    def __str__(self) -> str:
        return (
            f"FFmpegConfig(ffmpeg={self.ffmpeg_path or 'not found'}, "
            f"ffprobe={self.ffprobe_path or 'not found'})"
        )
