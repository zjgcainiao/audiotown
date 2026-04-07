from .base_format import BaseFormatPolicy
from audiotown.video.consts import MediaAction


class DefaultPolicy(BaseFormatPolicy):
    def evaluate(self, probe_data: dict) -> MediaAction:
        return MediaAction.SKIP

    def apply(self, media, decision):
        return 