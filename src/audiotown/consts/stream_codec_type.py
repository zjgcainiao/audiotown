from __future__ import annotations
from enum import StrEnum


class StreamCodecType(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"
    SUBTITLE = "subtitle"
    ATTACHMENT = "attachment"
    DATA = "data"
    METADATA = "metadata"

    def get_stream_specifier(self, codec_type: StreamCodecType, default_output_index: int) -> str | None:
        # Map your Enum to FFmpeg shorthand specifiers
        specifier_map = {
            StreamCodecType.VIDEO: "v",
            StreamCodecType.AUDIO: "a",
            StreamCodecType.SUBTITLE: "s",
            StreamCodecType.DATA: "d",
            StreamCodecType.ATTACHMENT: "t",
        }
        
        st_type = specifier_map.get(codec_type)
        return st_type