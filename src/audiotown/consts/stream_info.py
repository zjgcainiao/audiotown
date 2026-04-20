from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import  Any


@dataclass(slots=True)
class StreamInfo:
    file: Path
    streams: list[dict[str, Any]] = field(default_factory=list)
    format: dict[str, Any] = field(default_factory=dict)


    @classmethod
    def from_ffprobe_json(cls, file:Path, raw_json: dict[str, Any]) -> StreamInfo:
        """
        Safely extracts 'streams' and 'format' from the raw ffprobe JSON.
        """
        # We use .get() to avoid KeyErrors if ffprobe fails to find a stream
        streams = raw_json.get("streams", [])
        format_info = raw_json.get("format", {})
        return cls(file=file, streams=streams, format=format_info)

