from enum import StrEnum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from .media_action import MediaAction
from audiotown.consts.stream_info import StreamInfo
from .video_stream_spec import VideoStreamSpec
from .subtitle_stream_spec import SubtitleStreamSpec
from .video_container import VideoContainer
from .audio_stream_spec import AudioStreamSpec


@dataclass(slots=True)
class MediaInfo:
    file: Path
    container_name: VideoContainer | None = None
    format_name: str | None = None
    duration_sec: float | None = None
    size_bytes: int | None = None
    bit_rate: int | None = None
    video_streams: list[VideoStreamSpec] = field(default_factory=list)
    audio_streams: list[AudioStreamSpec] = field(default_factory=list)
    subtitle_streams: list[SubtitleStreamSpec] = field(default_factory=list)
    # raw_stream_info: StreamInfo | None = None
    is_readable: bool = field(default=True)
    error: Optional[str] = None

    @property
    def bit_rate_kbps(self) -> float | None:
        if self.bit_rate is None:
            return None
        return float(self.bit_rate/1000) or None
    
    @property
    def has_playable_av(self) -> bool:
        return self.has_video and self.has_audio
    
    @property
    def video_stream_count(self) -> int:
        return len(self.video_streams)

    @property
    def audio_stream_count(self) -> int:
        return len(self.audio_streams)

    @property
    def subtitle_stream_count(self) -> int:
        return len(self.subtitle_streams)

    @property
    def has_video(self) -> bool:
        return bool(self.video_streams)

    @property
    def has_audio(self) -> bool:
        return bool(self.audio_streams)

    @property
    def has_subtitles(self) -> bool:
        return bool(self.subtitle_streams)

    @property
    def first_video_stream(self) -> VideoStreamSpec | None:
        return self.video_streams[0] if self.video_streams else None

    @property
    def first_audio_stream(self) -> AudioStreamSpec | None:
        return self.audio_streams[0] if self.audio_streams else None

    @property
    def first_subtitle_stream(self) -> SubtitleStreamSpec | None:
        return self.subtitle_streams[0] if self.subtitle_streams else None 
    
    @property
    def audio_codec_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for stream in self.audio_streams:
            codec = stream.codec_name or "unknown"
            counts[codec] = counts.get(codec, 0) + 1
        return counts

