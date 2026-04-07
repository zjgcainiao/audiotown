from .base_format import BaseFormatPolicy
from audiotown.video.consts import MediaAction
from audiotown.video.consts import MediaInfo, PolicyDecision

class MKVPolicy(BaseFormatPolicy):
    # def evaluate(self, probe_data: dict) -> MediaAction:
    #     v_codec = probe_data['streams'][0].get('codec_name', '')
    #     a_codec = probe_data['streams'][1].get('codec_name', '')
        
    #     # The "Customs Officer" Check
    #     if v_codec in ['h264', 'hevc'] and a_codec in ['aac', 'alac', 'mp3']:
    #         return MediaAction.REMUX  # Fast path
    #     return MediaAction.TRANSCODE  # Heavy path

    def apply(self, media: MediaInfo, decision: PolicyDecision) -> None:
        decision.source_container = "mkv"

        video = media.first_video_stream
        audio = media.first_audio_stream

        if video and video.codec_name not in {"h264", "hevc"}:
            decision.video_must_transcode = True

        if audio and audio.codec_name not in {"aac", "alac", "mp3"}:
            decision.audio_must_transcode = True

        if media.subtitle_streams:
            decision.subtitle_mode = "mov_text_or_drop"

        decision.repair_notes.append("MKV source inspected for Apple-safe MP4 output.")