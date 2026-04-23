from audiotown.consts.video import VideoRecord, PolicyDecision, SubtitleMode, VideoCodec, AppleCompatibilityLevel, SpeedProfile, QualityProfile, VideoContainer, PixelFormat
from audiotown.consts.audio import AudioFormat
from audiotown.consts.video.media_action import MediaAction
from audiotown.consts.video.video_encoder import VideoEncoder

class AppleSafeMp4TargetPolicy:
    def apply(self, video_record: VideoRecord, decision: PolicyDecision) -> None:
        decision.container = VideoContainer.MP4 # "mp4"
        if not decision.audio_stream_decisions and not decision.video_stream_decisions:
            if decision.action != MediaAction.SKIP:
                decision.video_codec = VideoCodec.HEVC 
                decision.video_encoder = VideoEncoder.LIBX265 
                decision.audio_format = AudioFormat.AAC 
                decision.pixel_format = PixelFormat.YUV420P
        # mutiple video streams are reserved for mkv files.
        # otherwise, use the policy-decision level fields like decision.video_codec, decison.video_encoder,
        decision.subtitle_mode = SubtitleMode.MOV_TEXT_OR_DROP # "mov_text_or_drop"
        decision.compatibility_level = AppleCompatibilityLevel.GENERAL_SAFE # support HEVC now
        decision.quality_profile = QualityProfile.BALANCED
        decision.speed_profile = SpeedProfile.MEDIUM

        decision.preserve_metadata = True
        decision.preserve_chapters = True
        decision.faststart = True