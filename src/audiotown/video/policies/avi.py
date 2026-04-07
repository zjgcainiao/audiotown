from .base_format import BaseFormatPolicy
from audiotown.video.consts import MediaInfo, PolicyDecision


class AVIPolicy(BaseFormatPolicy):

    def apply(self, media: MediaInfo, decision: PolicyDecision): 
        file = media.file
        if file is None:
            return 
        suffix = media.file.suffix.lower()

        decision.needs_genpts = True

        decision.repair_notes.append("Avi source detected; generated timestamps.")