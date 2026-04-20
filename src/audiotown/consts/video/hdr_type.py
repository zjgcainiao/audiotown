from enum import StrEnum


class HDRType(StrEnum):
    SDR = "sdr"
    HDR10 = "hdr10"
    HLG = "hlg"
    UNKNOWN_HDR = "unknown_hdr"