from dataclasses import dataclass, field
from .video_codec import VideoCodec
from .pixel_format_policy import PixelFormatPolicy, PixelFormat
from audiotown.utils import safe_cast
from typing import Any

@dataclass(slots=True)
class VideoStreamSpec:
    codec_name: str | None
    codec_tag_string: str | None
    width: int | None
    height: int | None
    pix_fmt: PixelFormat | None
    profile: str | None
    level: int | None
    bit_rate: int | None
    avg_frame_rate: str | None
    r_frame_rate: str | None
    duration_sec: float | None
    lang: str|None
    
    # HDR fields
    color_primaries :str | None
    color_transfer : str | None
    color_space: str | None

    # other tehcnial fields
    color_range: str | None
    chroma_location: str | None
    sample_aspect_ratio: str | None
    display_aspect_ratio: str | None
    field_order: str | None
    has_b_frame: int | None
    
    view_ids_available: str | None
    view_pos_available: str | None

    coded_width: int | None
    coded_height:int | None
    # raw dump
    raw_tags: dict[str, Any] | None = None 
    

    stream_index: int | None = field(default=None)
    is_default: bool = field(default=False)

    # to mark if a mp4 is a raw or compatible apple-safe mp4
    is_avc: bool | None = field(default=None)  # Raw ffprobe flag


    @property
    def resolution(self) -> str | None:
        """
            Returns a string of width x height as resolution. Can be None
        """
        if self.width is None or self.height is None:
            return None
        if self.width <= 0 or self.height <= 0:
            return None
        return f"{self.width}x{self.height}"
    
    @property
    def resolution_tuple(self) -> tuple[int, int] | None:
        if self.width is None or self.height is None:
            return None
        if self.width <= 0 or self.height <= 0:
            return None
        return self.width, self.height
    

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
        Apple devices require: 
          1. AVCC packing (is_avc=True), 
          2. YUV420P, and, 
          3. Constant Frame Rate (is_vrf=False).
        """
        # 1. Must be H.264 (or HEVC, but you're targeting h264 for v1.1)
        if self.codec_name not in [VideoCodec.H264.ffprobe_name, ]: # "avc1"
            return False
        
        if self.level is not None and self.level > 41:
            return False
        
        # 2. Must NOT be Annex-B (is_avc: false)
        if self.is_annex_b:
            return False
            
        # 3. Must be YUV420P. 8bit
        if self.pix_fmt != PixelFormatPolicy.YUV420P_SAFE:
            return False
            
        # 4. Should be Constant Frame Rate (cfr)
        if self.is_vfr:
            return False
            
        return True
    
    @property
    def bit_depth(self) -> int | None:
        """
        Best-effort bit depth guess from pix_fmt.
        Examples:
            yuv420p      -> 8
            yuv420p10le  -> 10
            yuv422p12le  -> 12
        """
        if not self.pix_fmt:
            return None

        pf = self.pix_fmt
        if pf is None:
            return None
        return pf.bit_depth
    
    @property
    def is_hdr(self) -> bool:
        transfer = (self.color_transfer or "").lower()
        return transfer in {"smpte2084", "arib-std-b67"}

    @property
    def hdr_type(self) -> str:
        transfer = (self.color_transfer or "").lower()
        if transfer == "smpte2084":
            return "hdr10"
        if transfer == "arib-std-b67":
            return "hlg"
        return "sdr"

    @property
    def is_widescreen(self, threshold=1.6):
        """
        Determine if a video is widescreen.
        
        Args:
            width: Video width in pixels
            height: Video height in pixels
            threshold: Minimum aspect ratio for widescreen (default 1.6)
        
        Returns:
            bool: True if widescreen, False otherwise
        """
        if not self.height:
            return False
        aspect_ratio = safe_cast(self.width, int) or 0 / self.height
        return aspect_ratio >= threshold