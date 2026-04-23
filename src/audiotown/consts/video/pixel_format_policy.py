from __future__ import annotations
from enum import StrEnum

class PixelFormatPolicy(StrEnum):
    PRESERVE = "preserve"
    YUV420P_SAFE = "yuv420p"
    YUV420P_10LE ='yuv420p10le'


class PixelFormat(StrEnum):
    YUV420P = "yuv420p"
    YUV420P10LE = "yuv420p10le"
    YUV420P12LE = "yuv420p12le"
    YUV420P16LE = "yuv420p16le"

    YUV422P = "yuv422p"
    YUV422P10LE = "yuv422p10le"
    YUV422P12LE = "yuv422p12le"
    YUV422P16LE = "yuv422p16le"

    YUV444P = "yuv444p"
    YUV444P10LE = "yuv444p10le"
    YUV444P12LE = "yuv444p12le"
    YUV444P16LE = "yuv444p16le"

    NV12 = "nv12"
    NV21 = "nv21"
    P010LE = "p010le"
    P012LE = "p012le"
    P016LE = "p016le"

    GRAY = "gray"
    GRAY8 = "gray8"
    GRAY10LE = "gray10le"
    GRAY12LE = "gray12le"
    GRAY16LE = "gray16le"

    RGB24 = "rgb24"
    RGB48LE = "rgb48le"
    BGR24 = "bgr24"
    BGR48LE = "bgr48le"

    YUVA420P = "yuva420p"
    YUVA420P10LE = "yuva420p10le"

    UNKNOWN = "unknown"



    @classmethod
    def from_raw(cls, value: str | None) -> PixelFormat | None:
        if not value:
            return None
        try:
            return cls(value.lower())
        except ValueError:
            return None
    
    @classmethod
    def eight_bit_formats(cls) -> set[PixelFormat]:
        return {
            cls.YUV420P,
            cls.YUV422P,
            cls.YUV444P,
            cls.NV12,
            cls.NV21,
            cls.GRAY,
            cls.GRAY8,
            cls.RGB24,
            cls.BGR24,
            cls.YUVA420P,
        }

    @classmethod
    def ten_bit_formats(cls) -> set[PixelFormat]:
        return {
            cls.YUV420P10LE,
            cls.YUV422P10LE,
            cls.YUV444P10LE,
            cls.P010LE,
            cls.GRAY10LE,
            cls.YUVA420P10LE,
        }

    @classmethod
    def twelve_bit_formats(cls) -> set[PixelFormat]:
        return {
            cls.YUV420P12LE,
            cls.YUV422P12LE,
            cls.YUV444P12LE,
            cls.P012LE,
            cls.GRAY12LE,
        }

    @classmethod
    def sixteen_bit_formats(cls) -> set[PixelFormat]:
        return {
            cls.YUV420P16LE,
            cls.YUV422P16LE,
            cls.YUV444P16LE,
            cls.P016LE,
            cls.GRAY16LE,
            cls.RGB48LE,
            cls.BGR48LE,
        }


    @classmethod
    def yuv420_formats(cls) -> set["PixelFormat"]:
        return {
            cls.YUV420P,
            cls.YUV420P10LE,
            cls.YUV420P12LE,
            cls.YUV420P16LE,
            cls.NV12,
            cls.NV21,
            cls.P010LE,
            cls.P012LE,
            cls.P016LE,
            cls.YUVA420P,
            cls.YUVA420P10LE,
        }   
    

    @property
    def is_420(self) -> bool:
        return self in type(self).yuv420_formats()
         
    @property
    def is_8bit(self) -> bool:
        if self in PixelFormat.eight_bit_formats():
            return True
        else: 
            return False
    @property
    def is_10bit(self) -> bool:
        if self in PixelFormat.eight_bit_formats():
            return True
        else: 
            return False
    
    @property
    def is_12bit(self) -> bool:
        if self in PixelFormat.twelve_bit_formats():
            return True
        else: 
            return False
    @property
    def is_16bit(self) -> bool:
        if self in PixelFormat.twelve_bit_formats():
            return True
        else: 
            return False
    
    @property
    def bit_depth(self) -> int | None:
        if self in self.eight_bit_formats():
            return 8
        if self in self.ten_bit_formats():
            return 10
        if self in self.twelve_bit_formats():
            return 12
        if self in self.sixteen_bit_formats():
            return 16
        return None


# This is even better if you do not want to pretend every possible pix_fmt is fully captured by an enum.
class PixelFormatGroups:
    EIGHT_BIT: frozenset[str] = frozenset({
        "yuv420p",
        "yuv422p",
        "yuv444p",
        "nv12",
        "nv21",
        "rgb24",
        "bgr24",
        "gray",
        "gray8",
        "yuva420p",
    })

    TEN_BIT: frozenset[str] = frozenset({
        "yuv420p10le",
        "yuv422p10le",
        "yuv444p10le",
        "p010le",
    })

    TWELVE_BIT: frozenset[str] = frozenset({
        "yuv420p12le",
        "yuv422p12le",
        "yuv444p12le",
        "p012le",
    })

    YUV420_FAMILY: frozenset[str] = frozenset({
        "yuv420p",
        "yuv420p10le",
        "yuv420p12le",
        "nv12",
        "nv21",
        "p010le",
        "p012le",
        "yuva420p",
    })