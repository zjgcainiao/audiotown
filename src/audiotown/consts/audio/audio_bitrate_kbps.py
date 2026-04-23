from __future__ import annotations
from enum import StrEnum


class AudioBitRateKbps(StrEnum):
    LOW="128k"
    MEDIUM="192k"
    HIGH="256k"


    @classmethod
    def choose_aac_bitrate_kbps_output(cls, channels: int | None, source_bitrate_bps: int | None) -> AudioBitRateKbps:
        if channels is None:
            return cls.MEDIUM

        if channels >= 6:
            return cls.HIGH

        if channels == 2:
            if source_bitrate_bps is not None and source_bitrate_bps >= 220_000:
                return cls.HIGH
            return cls.MEDIUM

        return cls.LOW