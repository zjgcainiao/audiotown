
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass(frozen=True, slots=True)
class AudioStream:
    streams: List[Dict[str, Any]] = field(default_factory=list)
    format: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_ffprobe_json(cls, data: Dict[str, Any]) -> "AudioStream":
        """
        Safely extracts 'streams' and 'format' from the raw ffprobe JSON.
        """
        # We use .get() to avoid KeyErrors if ffprobe fails to find a stream
        streams = data.get("streams", [])
        format_info = data.get("format", {})
        return cls(streams=streams, format=format_info)

