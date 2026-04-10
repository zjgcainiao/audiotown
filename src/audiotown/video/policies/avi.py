from .base_format import BaseFormatPolicy
from audiotown.consts.video import MediaInfo, PolicyDecision, MediaAction

class AVIPolicy(BaseFormatPolicy):

    def apply(self, media: MediaInfo, decision: PolicyDecision) -> None: 
        file = media.file
        if file is None:
            return 
        suffix = media.file.suffix.lower()

        decision.action = MediaAction.TRANSCODE
        decision.needs_genpts = True
        decision.repair_notes.append("Avi source detected; generated timestamps.")