from email.policy import Policy

from .base_format import BaseFormatPolicy
from audiotown.consts.video import VideoRecord, PolicyDecision

class VOBPolicy(BaseFormatPolicy):

    def apply(self, video_record: VideoRecord, decision: PolicyDecision):
        pass