from .base_format import BaseFormatPolicy
from audiotown.video.consts import MediaAction


class RMVBPolicy(BaseFormatPolicy):
    def evaluate(self, probe_data: dict) -> MediaAction:
        return MediaAction.TRANSCODE
