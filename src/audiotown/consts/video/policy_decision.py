from dataclasses import dataclass, field
from enum import StrEnum
from .media_action import MediaAction
from .media_action_mode import MediaActionMode
from .subtitle_mode import SubtitleMode
from .speed_profile import SpeedProfile
from .video_container import VideoContainer
from .video_encoder import VideoEncoder, VideoEncoderSpec
from .video_codec import VideoCodec
from .quality_profile import QualityProfile
from .pixel_format_policy import  PixelFormat
from .apple_compatiblity_level import AppleCompatibilityLevel
from audiotown.consts.audio.audio_format import AudioFormat



class StreamDecision(StrEnum):
    TRANSCODE = "transcode"
    COPY = "copy"
    DROP = "drop"

@dataclass(slots=True)
class VideoStreamDecision:
    stream_index: int
    mode: StreamDecision  # "copy" | "transcode"
    codec: VideoCodec | None = None
    encoder: VideoEncoder | None = None
    pixel_format: PixelFormat | None = None
    is_vfr: bool = False
    target_frame_rate: str | None = None
    tag: str | None = None
@dataclass(slots=True)
class AudioStreamDecision:
    stream_index: int
    mode: StreamDecision  # "copy" | "transcode" | "drop"
    # codec: AudioCodec | None = None
    # encoder: AudioEncoder | None = None
    audio_format: AudioFormat | None = None
    bitrate: str | None = None
    enforce_two_channels: bool = False
    make_default: bool = False

@dataclass(slots=True)
class PolicyDecision:
    action: MediaAction| None = None
    container: VideoContainer | None = None
    video_codec: VideoCodec | None = None
    video_encoder: VideoEncoder | None = None
    audio_format: AudioFormat | None = None
    is_speed_mode_on: bool = False # use videotoolbox if speed mode is on
    does_max_compatiblity: bool = False

    subtitle_mode: SubtitleMode | None = None
    
    # semantic output behavior
    compatibility_level: AppleCompatibilityLevel | None = None      # "apple_safe"
    pixel_format: PixelFormat | None = None      # "preserve" / "yuv420p_safe"
    
    # new fields to do fine-grained stream-level transcode/copy control
    video_stream_decisions: list[VideoStreamDecision] = field(default_factory=list) # VideoStreamDecision | None = None
    audio_stream_decisions: list[AudioStreamDecision] = field(default_factory=list)
    
    # "balanced"
    quality_profile: QualityProfile | None = None         
    # "medium"
    speed_profile: SpeedProfile | None = None        
    needs_genpts: bool = False
    preserve_metadata: bool = True
    preserve_chapters: bool = True
    faststart: bool = False
    prefer_english_audio_default: bool = False
    prefer_english_subtitle_default: bool = False
    normalize_missing_language_tags: bool = False
    is_variable_frame_rate: bool = False
    target_frame_rate: str | None = None
    ignore_unknown: bool = False

    warnings: list[str] = field(default_factory=list)
    repair_notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


