
from dataclasses import dataclass

@dataclass(slots=True)
class ProbeSummary:
    container: str
    video_codec: str
    audio_codec: str
    has_video: bool
    has_audio: bool