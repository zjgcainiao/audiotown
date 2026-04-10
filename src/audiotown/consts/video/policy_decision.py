from dataclasses import dataclass, field
from .media_action import MediaAction
from .media_action_mode import MediaActionMode
from .subtitle_mode import SubtitleMode
from .speed_profile import SpeedProfile
from .video_container import VideoContainer
from .video_encoder import VideoEncoder, VideoEncoderSpec
from .video_codec import VideoCodec
from .quality_profile import QualityProfile
from .pixel_format_policy import PixelFormatPolicy
from .compatiblity_level import CompatibilityLevel
from audiotown.consts import AudioFormat


@dataclass(slots=True)
class PolicyDecision:
    action: MediaAction| None = None
    container: VideoContainer | None = None
    video_codec: VideoCodec | None = None
    video_encoder: VideoEncoder | None = None

    audio_format: AudioFormat | None = None
    subtitle_mode: SubtitleMode | None = None
    
    # semantic output behavior
    compatibility_level: CompatibilityLevel | None = None      # "apple_safe"
    pixel_format_policy: PixelFormatPolicy | None = None      # "preserve" / "yuv420p_safe"
    
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


