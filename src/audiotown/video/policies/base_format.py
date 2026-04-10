from abc import ABC, abstractmethod
from audiotown.consts.video import MediaInfo, PolicyDecision
from typing import Dict, List

class BaseFormatPolicy(ABC):
    # @abstractmethod
    # def evaluate(self, probe_data: dict) -> MediaAction:
    #     """Return the recommended action for this media file."""
    #     raise NotImplementedError
    
    @abstractmethod
    def apply(self, media: MediaInfo, decision: PolicyDecision) -> None:
        raise NotImplementedError

    # def get_conversion_flags(self, probe_data: dict) -> List[str]:
    #     """
    #     Translates probe findings into specific FFmpeg flags.
    #     This is where the '10-bit to 8-bit' logic lives.
    #     """
    #     flags = []
        
    #     # 1. The 10-bit Check (The Baywatch Fix)
    #     # We look into the video stream specifically
    #     video_stream = next((s for s in probe_data.get("streams", []) if s.get("codec_type") == "video"), {})
    #     pix_fmt = video_stream.get("pix_fmt", "")

    #     if "10" in pix_fmt or "12" in pix_fmt:
    #         # If it's high bit-depth, force 8-bit for Apple compatibility
    #         flags.extend(["-pix_fmt", "yuv420p"])
            
    #     return flags