from audiotown.consts.video import MediaInfo, PolicyDecision, SubtitleMode, VideoCodec, CompatibilityLevel, SpeedProfile, QualityProfile, PixelFormatPolicy, VideoContainer
from audiotown.consts import AudioFormat
from audiotown.consts.video.video_encoder import VideoEncoder

class AppleSafeMp4TargetPolicy:
    def apply(self, decision: PolicyDecision) -> None:
        decision.container = VideoContainer.MP4 # "mp4"

        decision.video_codec = VideoCodec.H264 # "h264"
        decision.video_encoder = VideoEncoder.LIBX264 # "libx264"
        decision.audio_format = AudioFormat.AAC # "aac"

        decision.subtitle_mode = SubtitleMode.MOV_TEXT_OR_DROP # "mov_text_or_drop"

        decision.compatibility_level = CompatibilityLevel.APPLE_SAFE
        decision.pixel_format_policy = PixelFormatPolicy.YUV420P_SAFE
        decision.quality_profile = QualityProfile.BALANCED
        decision.speed_profile = SpeedProfile.MEDIUM

        decision.preserve_metadata = True
        decision.preserve_chapters = True
        decision.faststart = True