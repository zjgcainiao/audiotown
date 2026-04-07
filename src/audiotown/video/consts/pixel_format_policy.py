from enum import StrEnum


class PixelFormatPolicy(StrEnum):
    PRESERVE = "preserve"
    YUV420P_SAFE = "yuv420p_safe"
    YUV420P_10LE ='yuv420p10le'