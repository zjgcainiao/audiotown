
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict

@dataclass(slots=True)
class AttachedPicSpec:
    stream_index: int | None
    codec_name: str | None # Could be mjpeg, png, etc.
    codec_type: str | None
    width: int | None
    height: int | None
    
    # Usually stored in tags like 'comment' or 'title' (e.g., "cover", "back")
    description: str| None = None
    raw_tags: dict[str, Any] | None  = None  # <--- The "Trash Can" for this specific stream

    @property
    def pic_resolution(self):
        if self.width is not None and self.height is not None:
            resolution=f"{self.width}x{self.height}"
            return resolution
        else:
            return None
