from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class AttachmentStreamSpec:
    stream_index: int | None
    file_name: str | None
    mime_type: str | None
    # Search stream['tags']['NUMBER_OF_BYTES'] for this
    size_bytes: int | None = None 
    lang: str | None = None
    raw_tags: dict[str, Any] | None  = None  # <--- The "Trash Can" for this specific stream
