from enum import StrEnum


class QualityTier(StrEnum):
    LOSSLESS_HIRES = "lossless_hires"
    LOSSLESS_CD = "lossless_cd"
    LOSSLESS_OTHER = "lossless_other"

    LOSSY_HIGH = "lossy_high"
    LOSSY_STANDARD = "lossy_standard"
    LOSSY_LOW = "lossy_low"
    LOSSY_UNKNOWN = "lossy_unknown"
    UNKNOWN = "unknown"