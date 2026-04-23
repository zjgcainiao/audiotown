from .base_format import BaseFormatPolicy

from audiotown.consts.video import VideoRecord, PolicyDecision, VideoCodec, VideoEncoder, MediaAction


class RMVBPolicy(BaseFormatPolicy):
    # def evaluate(self, video_record: VideoRecord) -> MediaAction:
    #     return MediaAction.TRANSCODE

    def apply(self, video_record: VideoRecord, decision: PolicyDecision) -> None:
        first_video = video_record.first_video_stream
        if first_video is not None:
            r_rate = first_video.r_frame_rate 
            avg_rate = first_video.avg_frame_rate
        
            if r_rate != avg_rate:
                decision.is_variable_frame_rate = True
                decision.target_frame_rate = r_rate
        
        decision.action = MediaAction.TRANSCODE
        decision.ignore_unknown = True
        decision.needs_genpts = True
        
        # new
        decision.video_codec = VideoCodec.HEVC
        decision.video_encoder = VideoEncoder.LIBX265
        
        decision.repair_notes.append("Legacy RMVB source detected; generated timestamps.")