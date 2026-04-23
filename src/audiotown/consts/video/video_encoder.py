from enum import StrEnum
from dataclasses import dataclass
from .video_codec import VideoCodec

class VideoEncoder(StrEnum):
    LIBX264 = "libx264"
    LIBX265 = "libx265"
    H264_VIDEOTOOLBOX = "h264_videotoolbox"
    HEVC_VIDEOTOOLBOX = "hevc_videotoolbox"
    
    @property
    def video_codec(self) -> "VideoCodec":
        if self in (VideoEncoder.LIBX264, VideoEncoder.H264_VIDEOTOOLBOX):
            return VideoCodec.H264
        if self in (VideoEncoder.LIBX265, VideoEncoder.HEVC_VIDEOTOOLBOX):
            return VideoCodec.HEVC
        raise ValueError(f"Unsupported video encoder: {self}")

    @classmethod
    def from_video_codec(
        cls,
        video_codec: VideoCodec,
        use_videotoolbox: bool = False,
    ) -> "VideoEncoder | None":
        if video_codec == VideoCodec.H264:
            return cls.H264_VIDEOTOOLBOX if use_videotoolbox else cls.LIBX264
        if video_codec == VideoCodec.HEVC:
            return cls.HEVC_VIDEOTOOLBOX if use_videotoolbox else cls.LIBX265
        # raise ValueError(f"No supported encoder mapping for codec: {video_codec}")
        return None



@dataclass(frozen=True, slots=True)
class VideoEncoderSpec:
    name: str
    codec_name: str
    is_hardware: bool
    supports_crf: bool
    supports_cq: bool
    supports_bitrate: bool
    preferred_extensions: tuple[str, ...] = ()

LIBX264 = VideoEncoderSpec(
    name="libx264",
    codec_name="h264",
    is_hardware=False,
    supports_crf=True,
    supports_cq=False,
    supports_bitrate=True,
    preferred_extensions=(".mp4", ".mkv", ".mov"),
)
LIBX265 = VideoEncoderSpec(
    name="libx265",
    codec_name="h265",
    is_hardware=False,
    supports_crf=True,
    supports_cq=False,
    supports_bitrate=True,
    preferred_extensions=(".mp4", ".mkv", ".mov"),
)

HEVC_VIDEOTOOLBOX = VideoEncoderSpec(
    name="hevc_videotoolbox",
    codec_name="hevc",
    is_hardware=True,
    supports_crf=False,
    supports_cq=True,
    supports_bitrate=True,
    preferred_extensions=(".mp4", ".mkv", ".mov"),
)