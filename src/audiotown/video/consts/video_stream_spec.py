from dataclasses import dataclass, field

@dataclass(slots=True)
class VideoStreamSpec:
    codec_name: str | None
    width: int | None
    height: int | None
    pix_fmt: str | None
    profile: str | None
    level: int | None
    bit_rate: int | None
    avg_frame_rate: str | None
    r_frame_rate: str | None
    duration_sec: float | None
    stream_index: int | None = field(default=None)
    is_default : bool = field(default=False)