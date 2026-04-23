from .base_format import BaseFormatPolicy
from audiotown.consts.video import VideoRecord, PolicyDecision, MediaAction

class AVIPolicy(BaseFormatPolicy):

    def apply(self, video_record:VideoRecord, decision: PolicyDecision) -> None: 
        file = video_record.file
        if file is None:
            return 
        suffix = video_record.file.suffix.lower()

        decision.action = MediaAction.TRANSCODE
        decision.needs_genpts = True
        decision.repair_notes.append("Avi source detected; generated timestamps.")