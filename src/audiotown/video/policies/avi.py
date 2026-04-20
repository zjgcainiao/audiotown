from .base_format import BaseFormatPolicy
from audiotown.consts.video import VideoRecord, PolicyDecision, MediaAction

class AVIPolicy(BaseFormatPolicy):

    def apply(self, media:VideoRecord, decision: PolicyDecision) -> None: 
        file = media.file
        if file is None:
            return 
        suffix = media.file.suffix.lower()

        decision.action = MediaAction.TRANSCODE
        decision.needs_genpts = True
        decision.repair_notes.append("Avi source detected; generated timestamps.")