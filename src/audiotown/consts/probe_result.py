from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import subprocess
from .audio_stream import AudioStream
from .stream_info import StreamInfo


@dataclass(frozen=True, slots=True)
class ProbeResult:
    file_path: Path
    success: bool
    # existing audio_stream. future ProbedMedia
    stream_info: Optional[StreamInfo] = None
    error: Optional[str] = None
