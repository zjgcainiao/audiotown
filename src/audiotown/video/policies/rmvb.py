from networkx import descendants

from .base_format import BaseFormatPolicy
from audiotown.consts.video import MediaAction
from audiotown.consts.video import VideoRecord, PolicyDecision


class RMVBPolicy(BaseFormatPolicy):
    def evaluate(self, probe_data: dict) -> MediaAction:
        return MediaAction.TRANSCODE

    def apply(self, media, decision):
        first_video = media.first_video_stream
        if first_video is not None:
            r_rate = first_video.r_frame_rate 
            avg_rate = first_video.avg_frame_rate
        
            if r_rate != avg_rate:
                decision.is_variable_frame_rate = True
                decision.target_frame_rate = r_rate
        
        decision.action = MediaAction.TRANSCODE
        decision.ignore_unknown = True
        decision.needs_genpts = True
        
        decision.repair_notes.append("Legacy RMVB source detected; generated timestamps.")