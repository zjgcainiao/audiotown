from audiotown.consts.video import VideoRecord, PolicyDecision, SubtitleMode, VideoCodec, AppleCompatibilityLevel, SpeedProfile, QualityProfile, VideoContainer, PixelFormat
from audiotown.consts.audio import AudioFormat
from audiotown.consts.video.media_action import MediaAction
from audiotown.consts.video.policy_decision import SubtitleStreamDecision
from audiotown.consts.video.video_encoder import VideoEncoder

class AppleSafeMp4TargetPolicy:
    def apply(self, video_record: VideoRecord, decision: PolicyDecision) -> None:
        decision.container = VideoContainer.MP4 # "mp4"
        # if not decision.audio_stream_decisions and not decision.video_stream_decisions:
        #     if decision.action != MediaAction.SKIP:
        #         decision.video_codec = VideoCodec.HEVC 
        #         decision.video_encoder = VideoEncoder.LIBX265 
        #         decision.audio_format = AudioFormat.AAC 
        #         decision.pixel_format = PixelFormat.YUV420P
        # mutiple video streams are reserved for mkv files.
        # otherwise, use the policy-decision level fields like decision.video_codec, decison.video_encoder,
        decision.subtitle_mode = SubtitleMode.MOV_TEXT # "mov_text_or_drop"
        

        decision.compatibility_level = AppleCompatibilityLevel.GENERAL_SAFE # support HEVC now
        decision.quality_profile = QualityProfile.BALANCED
        decision.speed_profile = SpeedProfile.MEDIUM

        decision.preserve_metadata = True
        decision.preserve_chapters = True


        decision.prefer_english_audio_default=True
        decision.prefer_english_subtitle_default=True

        # Mandatory Global Standard (Always true for MKV -> MP4 conversion)
        decision.faststart = True

    def _build_subtitle_stream_decisions(self, video_record:VideoRecord, decision: PolicyDecision) -> None:
        if not video_record.has_subtitle:
            decision.subtitle_stream_decisions=[]
            return

        for sub in video_record.subtitle_streams:
            if sub.is_mp4_text_compatible:
                sub_mode = SubtitleMode.MOV_TEXT
            else:
                sub_mode = SubtitleMode.DROP
            decision.subtitle_stream_decisions.append(
                SubtitleStreamDecision(
                    stream_index=sub.stream_index or 0,
                    mode=sub_mode,
                    make_default=False
                )
            )
        