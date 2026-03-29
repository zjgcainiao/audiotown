
from dataclasses import dataclass, field
from .audio_record import AudioRecord
from audiotown.utils import to_int

@dataclass(slots=True)
class DuplicateGroup:
    records: list[AudioRecord] = field(default_factory=list)
    key: str = ""
    count: int = 0
    size_bytes: int = 0

    @property
    def waste_size(self) -> int:
        if len(self.records) < 2:
            return 0
        # 1. Sort by Quality (Lossless first, then High Bitrate)
        # This ensures the 'Best' file is at index 0
        records = self.records
        sorted_recs = sorted(
            self.records,
            key=lambda x: (not x.audio_format.is_lossless, -to_int(x.bitrate_bps)),
        )

        # 2. Sum up every file EXCEPT the first one (the keeper)
        return sum(rec.size_bytes for rec in sorted_recs[1:])