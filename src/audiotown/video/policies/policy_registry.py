from pathlib import Path

from audiotown.video.policies.avi import AVIPolicy
from .mkv import MKVPolicy
from .rmvb import RMVBPolicy
from .default import DefaultPolicy
from .base_format import BaseFormatPolicy


class PolicyRegistry:
    def get_policy_for_path(self, file_path: Path) -> BaseFormatPolicy:
        ext = file_path.suffix.lower()
        if ext == ".avi":
            return AVIPolicy()
        if ext == ".mkv":
            return MKVPolicy()
        if ext == ".rmvb":
            return RMVBPolicy()

        return DefaultPolicy()
