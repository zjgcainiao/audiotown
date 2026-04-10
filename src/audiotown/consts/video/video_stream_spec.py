from dataclasses import dataclass, field
from .video_codec import VideoCodec
from .pixel_format_policy import PixelFormatPolicy
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
    is_default: bool = field(default=False)
    is_avc: bool | None = field(default=None)  # Raw ffprobe flag

    @property
    def bit_rate_kbps(self) -> float | None:
        if self.bit_rate is None:
            return None
        else:
            return round(float(self.bit_rate / 1000.0), 1)

    @property
    def avg_frame_rate_formatted(self) -> str:
        return self.format_fps(self.avg_frame_rate)

    @property
    def r_frame_rate_formatted(self) -> str:
        return self.format_fps(self.r_frame_rate)

    def format_fps(self, fps: str | None) -> str:
        if not fps:
            return "?"
        if "/" in fps:
            num, den = fps.split("/", 1)
            try:
                return f"{float(num) / float(den):.3f}"
            except (ValueError, ZeroDivisionError):
                return fps
        return fps

    @property
    def is_annex_b(self) -> bool:
        """
        Logic for 'is this a raw bitstream?'
        In MP4, is_avc=False means Annex-B. 
        In RMVB/AVI, it's essentially always Annex-B/Raw behavior.
        """
        if self.is_avc is False:
            return True
        return False
    
    @property
    def is_vfr(self) -> bool:
        # Fixed logic: If they don't match, it's Variable Frame Rate
        if not self.r_frame_rate or not self.avg_frame_rate:
            return False
        return self.r_frame_rate != self.avg_frame_rate

    @property
    def is_apple_ready(self) -> bool:
        """
        An unvarnished assessment of compatibility.
        Apple devices require: AVCC packing (is_avc=True), YUV420P, and Constant Frame Rate.
        """
        # 1. Must be H.264 (or HEVC, but you're targeting h264 for v1.1)
        if self.codec_name not in [VideoCodec.H264.ffprobe_name, ]: # "avc1"
            return False
            
        # 2. Must NOT be Annex-B (is_avc: false)
        if self.is_annex_b:
            return False
            
        # 3. Must be YUV420P
        if self.pix_fmt != PixelFormatPolicy.YUV420P_SAFE:
            return False
            
        # 4. Should be Constant Frame Rate (cfr)
        if self.is_vfr:
            return False
            
        return True