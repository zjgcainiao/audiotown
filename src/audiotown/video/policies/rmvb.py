from .base_format import BaseFormatPolicy
from audiotown.video.consts import MediaAction
from audiotown.video.consts import MediaInfo, PolicyDecision


class RMVBPolicy(BaseFormatPolicy):
    def evaluate(self, probe_data: dict) -> MediaAction:
        return MediaAction.TRANSCODE

    def apply(self, media, decision):

        decision.needs_genpts = True

        decision.repair_notes.append("Legacy RMVB source detected; generated timestamps.")