# from enum import StrEnum
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field

from audiotown.consts.lang.lang_map import LANGUAGE_MAP
from collections import defaultdict
# from audiotown.consts.stream_info import StreamInfo
from .video_stream_spec import VideoStreamSpec
from .subtitle_stream_spec import SubtitleStreamSpec
from .video_container import VideoContainer
from .audio_stream_spec import AudioStreamSpec
from .apple_compatibility import AppleCompatibility
from audiotown.consts.basics.attached_pic_spec import AttachedPicSpec
from .attachment_stream_spec import AttachmentStreamSpec
from itertools import chain
from audiotown.consts.lang.lang_map import LANGUAGE_MAP, map_language

@dataclass(slots=True)  
class VideoRecord:
    file: Path
    container_name: VideoContainer | None = None
    format_name: str | None = None
    nb_streams: int | None = None
    duration_sec: float | None = None
    size_bytes: int | None = None
    bit_rate: int | None = None
    video_streams: list[VideoStreamSpec] = field(default_factory=list)
    audio_streams: list[AudioStreamSpec] = field(default_factory=list)
    subtitle_streams: list[SubtitleStreamSpec] = field(default_factory=list)

    # raw_stream_info: StreamInfo | None = None
    is_readable: bool = field(default=True)
    error: Optional[str] = None

    # new field:
    attachment_streams: list[AttachmentStreamSpec] = field(default_factory=list)
    attached_pic_streams: list[AttachedPicSpec] = field(default_factory=list)
    probe_score: int | None = None
    raw_tags: dict[str, Any] | None = None

    @property
    def bitrate_kbps(self) -> float | None:
        if self.bit_rate is None:
            return None
        return float(self.bit_rate/1000) or None
    

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
    def attachment_stream_count(self) -> int:
        return len(self.attachment_streams)
    
    @property
    def attached_pic_stream_count(self) -> int:
        return len(self.attached_pic_streams)

    @property
    def has_playable_av(self) -> bool:
        return self.has_video and self.has_audio
    
    @property
    def has_video(self) -> bool:
        return bool(self.video_streams)

    @property
    def has_audio(self) -> bool:
        return bool(self.audio_streams)

    @property
    def has_subtitle(self) -> bool:
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
    def video_codec_count(self) -> dict[str, int]:
        counts: defaultdict[str, int] = defaultdict(int)
        if not self.video_stream_count:
            return dict()
        for stream in self.video_streams:
            codec = stream.codec_name or "unknown"
            counts[codec] += 1
        return dict(counts)
    @property
    def audio_codec_count(self) -> dict[str, int]:
        counts: defaultdict[str, int] = defaultdict(int)
        if not self.audio_stream_count:
            return dict()
        for stream in self.audio_streams:
            codec = stream.codec_name or "unknown"
            counts[codec] += 1
        return dict(counts)
    
    @property
    def subtitle_codec_count(self) -> dict[str, int]:
        if not self.subtitle_stream_count:
            return dict()
        counts: defaultdict[str, int] = defaultdict(int)
        for stream in self.subtitle_streams:
            codec = stream.codec_name or "unknown"
            counts[codec] += 1
        return dict(counts)

    @property
    def apple_compatibility(self) -> AppleCompatibility:
        """Check the general playback compatiblie in apple devices.
        The function checks the video codecs and audio codecs from each stream.
        subtitle stream
            - direct play
            - needs remux
            - needs transcode
            - unsupported
            - unknown

        Returns:
            AppleCompatibility: _description_
        """
        if not self.is_readable:
            return AppleCompatibility.UNKNOWN
        if not self.has_audio or not self.has_video:
            return AppleCompatibility.UNSUPPORTED_STRUCTURE
        if not self.has_playable_av:
            return AppleCompatibility.UNSUPPORTED_STRUCTURE
        if self.file.suffix is None or self.size_bytes is None or self.duration_sec is None:
            return AppleCompatibility.UNKNOWN
        if all(v.is_apple_ready for v in self.video_streams) and all(a.is_apple_ready for a in self.audio_streams):
            if self.container_name == VideoContainer.MP4:
                return AppleCompatibility.DIRECT_PLAY
            else: 
                return AppleCompatibility.NEEDS_REMUX
        else:
            if self.file.suffix.lower() in VideoContainer.supported_suffixes():
                return AppleCompatibility.NEEDS_TRANSCODE
            else: 
                return AppleCompatibility.UNSUPPORTED_STRUCTURE

    @property
    def languages(self) -> set[str | None]:
        """
        Returns a set of languages fetched from video and audio streams.
        Example: set("eng", "fre", "jpn")
        """
        if not self.is_readable:
            return set()

        # Combine streams into a single iterable
        streams = chain(
            self.video_streams if self.has_video else [],
            self.audio_streams if self.has_audio else []
        )

        # Use a set comprehension with the walrus operator for clarity and speed
        result =  {
            LANGUAGE_MAP.get(l.lower(), l.lower())  # Use mapped value or original
            for s in streams 
            if (l := getattr(s, 'lang', None)) and l.lower() != "und"
        }   
        return result  

    # @property
    # def languages(self) -> set:
    #     lang_list=set()
    #     if not self.is_readable:
    #         return lang_list

    #     if self.has_video:
    #         for stream in self.video_streams:
    #             lang = stream.lang
    #             if lang is not None and lang.lower() != "und":
    #                 lang_list.add(lang.lower())
    #     if self.has_audio:
    #         for stream in self.audio_streams:
    #             lang = stream.lang
    #             if lang is not None and lang.lower() != "und":
    #                 lang_list.add(lang.lower())
        
    #     return lang_list
            

