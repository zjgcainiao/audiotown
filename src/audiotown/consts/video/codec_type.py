from __future__ import annotations
from enum import StrEnum


class CodecType(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"
    SUBTITLE = "subtitle"
    ATTACHMENT = "attachment"
    DATA = "data"
    METADATA = "metadata"

    def get_stream_specifier(self, codec_type: CodecType, default_output_index: int) -> str | None:
        # Map your Enum to FFmpeg shorthand specifiers
        specifier_map = {
            CodecType.VIDEO: "v",
            CodecType.AUDIO: "a",
            CodecType.SUBTITLE: "s",
            CodecType.DATA: "d",
            CodecType.ATTACHMENT: "t",
        }
        
        st_type = specifier_map.get(codec_type)
        return st_type