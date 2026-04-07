
import shutil
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class FFmpegConfig:
    """
    Frozen configuration for FFmpeg and ffprobe executables.
    Defaults to system PATH lookup via shutil.which().
    """

    ffmpeg_path: Optional[str] = field(default=None)
    ffprobe_path: Optional[str] = field(default=None)

    # def __post_init__(self):
    #     # Optional: warn or raise if paths are missing (uncomment if desired)
    #     # if self.ffmpeg_path is None:
    #     #     raise ValueError("ffmpeg not found in PATH")
    #     # if self.ffprobe_path is None:
    #     #     raise ValueError("ffprobe not found in PATH")
    #     pass
    @classmethod
    def create(cls):
        """Factory method to find binaries in bundle or system."""
        
        def find_binary(name):
            # 1. Check if we are running in a PyInstaller bundle
            if hasattr(sys, '_MEIPASS'):
                # sys._MEIPASS is a string, so we cast it to Path
                bundle_path = Path(sys._MEIPASS) / "bin" / name
                if bundle_path.exists():
                    return str(bundle_path) # Most subprocesses prefer strings

            # 2. Check relative path during development
            # Current file: root/src/engine/types.py
            # .parent -> engine | .parent -> src | .parent -> root
            root_folder = Path(__file__).resolve().parent.parent.parent
            dev_path = root_folder / "bin" / name
            
            if dev_path.exists():
                return str(dev_path)

            # 3. Fallback to system PATH
            found = shutil.which(name)
            # Move logging here so you can see why it failed the first two
            # if not found:
            #     logger.error(f"Failed to find {name}. Tried bundle and {dev_path}")
            return str(found) if found else None

        return cls(
            ffmpeg_path=find_binary("ffmpeg"),
            ffprobe_path=find_binary("ffprobe")
        )

    @property
    def is_complete(self) -> bool:
        """True if both executables were found."""
        return self.ffmpeg_path is not None and self.ffprobe_path is not None
    

    def require_ffmpeg(self) -> str:
        if self.ffmpeg_path is None:
            raise RuntimeError("ffmpeg not found in PATH")
        return self.ffmpeg_path

    def require_ffprobe(self) -> str:
        if self.ffprobe_path is None:
            raise RuntimeError("ffprobe not found in PATH")
        return self.ffprobe_path

    def require_both(self) -> tuple[str, str]:
        return self.require_ffmpeg(), self.require_ffprobe()
    
    def __str__(self) -> str:
        return (
            f"FFmpegConfig(ffmpeg={self.ffmpeg_path or 'not found'}, "
            f"ffprobe={self.ffprobe_path or 'not found'})"
        )
