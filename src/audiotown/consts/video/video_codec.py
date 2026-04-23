from __future__ import annotations
from enum import Enum
# from .video_encoder import VideoEncoder

class VideoCodec(Enum):
    H264 = ("h264", True, "H.264 / AVC")
    HEVC = ("hevc", True, "H.265 / HEVC")
    AV1 = ("av1", True, "AOMedia Video 1")
    VP9 = ("vp9", True, "Google VP9")
    MPEG4 = ("mpeg4", True, "MPEG-4 Part 2")
    MPEG2 = ("mpeg2video", True, "MPEG-2 Video")
    VC1 = ("vc1", True, "VC-1")
    RV40 = ("rv40", True, "RealVideo 9/10")
    H263 = ("h263", True, "H.263")
    MJPEG = ("mjpeg", True, "Motion JPEG")
    
    # lossless (is_lossy=False)
    PRORES = ("prores", False, "Apple ProRes")
    FFV1 = ("ffv1", False, "FFV1 Lossless")
    UTVIDEO = ("utvideo", False, "Ut Video Lossless")

    def __init__(self, ffprobe_name: str, is_lossy: bool, description: str):
        self.ffprobe_name = ffprobe_name
        self.is_lossy = is_lossy
        self.description = description
   
    @property
    def is_legacy(self) -> bool:
        return self in {
            VideoCodec.MPEG2,
            VideoCodec.MPEG4,
            VideoCodec.VC1,
            VideoCodec.RV40,
            VideoCodec.H263,
            VideoCodec.MJPEG,
        }
    
    @property
    def is_modern(self) -> bool:
        return self in {
            type(self).H264,
            type(self).HEVC,
            type(self).AV1,
            type(self).VP9,
        }

    @property
    def is_lossless(self) -> bool:
        return not self.is_lossy  
    

    @classmethod
    def from_codec_name(cls, codec_name: str) -> VideoCodec | None:
        """Find the default format for a given codec_name (e.g. .h264 -> VideoCodec.H264)."""
        codec_name = codec_name.strip().lower()
        for member in cls:
            if member.ffprobe_name == codec_name:
                return member
        return None
#     @classmethod
#     def get_from_encoder(cls, video_encoder:VideoEncoder) -> VideoCodec:

#         codec = ENCODER_TO_VIDEO_CODEC[video_encoder]
#         return codec

# ENCODER_TO_VIDEO_CODEC = {
#     VideoEncoder.LIBX264: VideoCodec.H264,
#     VideoEncoder.H264_VIDEOTOOLBOX: VideoCodec.H264,
#     VideoEncoder.LIBX265: VideoCodec.HEVC,
#     VideoEncoder.HEVC_VIDEOTOOLBOX: VideoCodec.HEVC,
# }