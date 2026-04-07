from enum import Enum, StrEnum

class CodecType(StrEnum):
    VIDEO="video"
    AUDIO="audio"
    SUBTITLE="subtitle"
    ATTACHMENT="attachment"