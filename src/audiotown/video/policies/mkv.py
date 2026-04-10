from .base_format import BaseFormatPolicy
from audiotown.consts.video import MediaAction
from audiotown.consts.video import MediaInfo, PolicyDecision, VideoEncoder
from audiotown.consts import AudioFormat

class MKVPolicy(BaseFormatPolicy):
    def apply(self, media: MediaInfo, decision: PolicyDecision) -> None:
        video = media.first_video_stream
        if not video:
            # We don't process files without video streams in this pipeline
            return

        # 1. Evaluate Video Health
        # This checks for: Codec (H.264), PixFmt (yuv420p), packing (AVCC), and CFR.
        video_ready = video.is_apple_ready
        
        if not video_ready:
            decision.repair_notes.append(f"MKV Video transcode required: {video.codec_name}")
            # If the video is VFR (common in MKVs from handbrake/web-rips), 
            # we flag it for repair during the transcode process.
            if video.is_vfr:
                decision.is_variable_frame_rate = True
                decision.target_frame_rate = video.r_frame_rate
                decision.repair_notes.append("Fixed Variable Frame Rate issues.")

        # 2. Evaluate Audio Health (The 'all()' Perfectionist)
        audio_streams = media.audio_streams or []
        all_audio_ready = all(a.is_apple_ready for a in audio_streams)
        
        if not all_audio_ready:
            # Most MKVs use AC3, DTS, or FLAC. Apple prefers AAC in MP4.
            decision.repair_notes.append("MKV Audio normalization required (non-AAC detected).")

        # 3. Final Decision: The "Apple-Safe" Verdict
        # We only REMUX if every single A/V stream is already in its final form.
        if video_ready and all_audio_ready:
            decision.action = MediaAction.REMUX
            decision.repair_notes.append("High-quality remux: No re-encoding performed.")
        else:
            decision.action = MediaAction.TRANSCODE
            # Ensure we use our standard v1.1 targets
            decision.video_encoder = VideoEncoder.LIBX264
            decision.audio_format = AudioFormat.AAC

        # 4. Mandatory Global Standard (Always true for MKV -> MP4 conversion)
        decision.faststart = True