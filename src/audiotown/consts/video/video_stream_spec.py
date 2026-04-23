from dataclasses import dataclass, field
from .video_codec import VideoCodec
from .pixel_format_policy import  PixelFormat
from .resolution_semantic_label import STANDARD_RESOLUTIONS, ResolutionSemanticLabel
from audiotown.utils import safe_cast
from typing import Any
import logging

logger = logging.getLogger(__name__)


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
    
    def semantic_resolution_label(self, width: int | None = None, height: int | None = None) -> str | None:
        width = self.width if width is None else width
        height =self.height if height is None else height
        if width is None or height is None or width <= 0 or height <= 0:
            return None

        exact = STANDARD_RESOLUTIONS.get((width, height))
        if exact:
            return exact.long

        # Near 1080p
        if 1880 <= width <= 1920 and 1040 <= height <= 1088:
            if width == 1920 and height < 1080:
                return "1080-width cinematic"
            return "Near 1080p"

        # Near 720p
        if 1240 <= width <= 1280 and 688 <= height <= 736:
            return "Near 720p"

        # Common oddballs
        if width == 1440 and height == 1080:
            return "HD variant"
        if width == 1024 and height == 576:
            return "576p-class widescreen"
        if width == 960 and height == 720:
            return "Below 720p"

        # Broad fallback buckets
        if height >= 2160:
            return "4K-class or higher"
        if height >= 1440:
            return "1440p-class"
        if height >= 1080:
            return "1080p-class"
        if height >= 720:
            return "720p-class"
        if height >= 576:
            return "576p-class"
        if height >= 480:
            return "480p-class"
        if 340 <= height <= 376:
            return "360p-class"
        if 250 <= height <= 286:
            return "270p-class"

        return "Low resolution"
    
    
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
        if self.r_frame_rate == self.avg_frame_rate:
            return False
        try: 
            division = float(self.r_frame_rate) / float(self.avg_frame_rate)
            if 0.99 < division <1.01:
                return False
            else: 
                return True
        except Exception:
            return False

   
    
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
    
    @property
    def is_drm_protected(self):
        if self.codec_tag_string:
            if "drm" in self.codec_tag_string.lower():
                return True
        return False
    
    @property
    def is_apple_ready(self) -> bool:
        """
        Conservative video-only Apple compatibility check.

        Current rules:
        1. Codec must be H.264 or HEVC (H.265)
        2. Bitstream must not be Annex-B
        3. Pixel format must be 4:2:0
            - H.264: 8-bit only
            - HEVC: 8-bit or 10-bit
        4. Prefer constant frame rate
        """
        # 1. Codec must be H.264 or HEVC
        # logger.info(f"--- In the VideoStreamSpec, self.codec_name: {self.codec_name}...self.is_annex_b: {self.is_annex_b}.....self.pix_fmt: {self.pix_fmt}...self.bit_depth: {self.bit_depth}...self.is_vfr: {self.is_vfr}")
        # logger.info(f"---  .....self.r_frame_rate: {self.r_frame_rate}...self.avg_frame_rate: {self.avg_frame_rate}")
        if self.codec_name not in {
            VideoCodec.H264.ffprobe_name,
            VideoCodec.HEVC.ffprobe_name,
        }:
            return False

        # 2. Must not be Annex-B
        if self.is_annex_b:
            return False

        # 3. Pixel format / bit depth constraints
        if self.pix_fmt is None:
            return False

        # Must be 4:2:0 for Apple-safe output
        if not self.pix_fmt.is_420:
            return False

        bit_depth = self.pix_fmt.bit_depth
        if bit_depth is None:
            return False

        # H.264: keep conservative at 8-bit
        if self.codec_name == VideoCodec.H264.ffprobe_name:
            if bit_depth != 8:
                return False

        # HEVC: allow 8-bit and 10-bit
        elif self.codec_name == VideoCodec.HEVC.ffprobe_name:
            if bit_depth not in {8, 10}:
                return False

        # 4. Prefer constant frame rate
        if self.is_vfr:
            return False

        return True