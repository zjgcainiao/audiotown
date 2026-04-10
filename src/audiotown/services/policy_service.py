from pathlib import Path
from typing import Optional

from audiotown.consts.video.media_info import MediaInfo, VideoContainer
from audiotown.video.policies.avi import AVIPolicy
from audiotown.video.policies.mkv import MKVPolicy
from audiotown.video.policies.rmvb import RMVBPolicy
from audiotown.video.policies.default import DefaultPolicy
from audiotown.video.policies.base_format import BaseFormatPolicy
from audiotown.logger import logger, SessionLogger
import logging

class PolicyService:
    # 1. Define as a class-level constant with explicit type hints
    # This tells Pylance exactly what the keys and values are.
    _POLICY_MAP: dict[VideoContainer, type[BaseFormatPolicy]] = {
        VideoContainer.AVI: AVIPolicy,
        VideoContainer.MKV: MKVPolicy,
        VideoContainer.RMVB: RMVBPolicy,
    }

    def __init__(self, service_logger: SessionLogger = logger):
        self.selected_policy = DefaultPolicy()
        self.logger = service_logger
        self._POLICY_MAP  = {
        VideoContainer.AVI: AVIPolicy,
        VideoContainer.MKV: MKVPolicy,
        VideoContainer.RMVB: RMVBPolicy,
        # Add MP4 if you have a specific policy for it later
        }
        

    def get_policy_for_path(self, file_path: Path) -> BaseFormatPolicy:
        """Backup function based on file extension."""
        suffix = file_path.suffix.lower()
        
        # We find the matching container enum by suffix
        container = next((c for c in VideoContainer if c.suffix == suffix), None)
        
        # 3. Handle the None case explicitly before calling .get()
        # This prevents Pylance from complaining about passing 'None' to a dict key lookup
        if container is None:
            return DefaultPolicy()

        policy_class = self._POLICY_MAP.get(container, DefaultPolicy)
        return policy_class()

    def get_policy_based_on_media_info(self, media: MediaInfo) -> BaseFormatPolicy:
        """Primary selection based on probed container name."""
        if not media.has_playable_av:
            self.logger.regular_log(f"No playable streams found for {media.file.name}")
            return DefaultPolicy()

        if media.container_name is None:
            return DefaultPolicy()
        policy_class = self._POLICY_MAP.get(media.container_name, DefaultPolicy)
        
        # Update state and return
        self.selected_policy = policy_class()
        return self.selected_policy

    # def get_policy_for_path(self, file_path: Path) -> BaseFormatPolicy:
    #     suffix = file_path.suffix.lower()

    #     if suffix == VideoContainer.AVI.suffix:
    #         return AVIPolicy()
    #     if suffix == VideoContainer.MKV.suffix:
    #         return MKVPolicy()
    #     if suffix == VideoContainer.RMVB.suffix:
    #         return RMVBPolicy()
    #     return DefaultPolicy()

    # def get_policy_based_on_media_info(
    #     self, media: MediaInfo
    # ) -> BaseFormatPolicy | None:

    #     if not media.has_playable_av:
    #         self.selected_policy = None
    #     if media.container_name == VideoContainer.AVI:
    #         self.selected_policy = AVIPolicy()
    #     elif media.container_name == VideoContainer.RMVB:
    #         self.selected_policy = RMVBPolicy()
    #     elif media.container_name == VideoContainer.MKV:
    #         self.selected_policy =MKVPolicy()
    #     return self.selected_policy
