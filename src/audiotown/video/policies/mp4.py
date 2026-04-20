from .base_format import BaseFormatPolicy
from audiotown.consts.video import VideoRecord, PolicyDecision, MediaAction

class MP4Policy(BaseFormatPolicy):
    def apply(self, media:VideoRecord, decision: PolicyDecision) -> None:
        video = media.first_video_stream
        if not video:
            return

     # If the spec says it's not ready, we ensure transcoding is triggered
        if not video.is_apple_ready:
            if video.is_vfr:
                decision.is_variable_frame_rate = True
                decision.target_frame_rate = video.r_frame_rate

            # We add notes to the decision for logging
            decision.repair_notes.append(f"Video not ready: {video.codec_name}/{video.pix_fmt}")

        # 2. Check All Audio Streams
        # all() returns True if the list is empty, which is correct for silent videos
        audio_streams = media.audio_streams or []
        all_audio_ready = all(a.is_apple_ready for a in audio_streams)
        
        if not all_audio_ready:
            decision.repair_notes.append("One or more audio streams not AAC.")

        # 3. Final Decision: Is the whole file "Apple Ready"?
        if video.is_apple_ready and all_audio_ready:
            decision.action = MediaAction.REMUX
        else:
            decision.action = MediaAction.TRANSCODE