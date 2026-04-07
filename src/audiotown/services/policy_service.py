from pathlib import Path

from audiotown.video.consts.media_info import MediaInfo, VideoContainer
from audiotown.video.policies.avi import AVIPolicy
from audiotown.video.policies.mkv import MKVPolicy
from audiotown.video.policies.rmvb import RMVBPolicy
from audiotown.video.policies.default import DefaultPolicy
from audiotown.video.policies.base_format import BaseFormatPolicy
from audiotown.logger import logger, SessionLogger


class PolicyService:
    def __init__(self, service_logger: SessionLogger = logger):
        self.selected_policy = DefaultPolicy()
        self.logger = service_logger

    def get_policy_for_path(self, file_path: Path) -> BaseFormatPolicy:
        suffix = file_path.suffix.lower()

        if suffix == ".avi":
            return AVIPolicy()
        if suffix == ".mkv":
            return MKVPolicy()
        if suffix == ".rmvb":
            return RMVBPolicy()
        return DefaultPolicy()

    def get_policy_based_on_media_info(
        self, media: MediaInfo
    ) -> BaseFormatPolicy | None:
        if not media.has_playable_av:
            self.selected_policy = None
        if media.container_name == VideoContainer.AVI:
            self.selected_policy = AVIPolicy()
        elif media.container_name == VideoContainer.RMVB:
            self.selected_policy = RMVBPolicy()
        return self.selected_policy
