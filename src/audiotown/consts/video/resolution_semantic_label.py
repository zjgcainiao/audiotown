from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ResolutionSemanticLabel:
    short: str
    long: str | None = None


STANDARD_RESOLUTIONS: dict[tuple[int, int], ResolutionSemanticLabel] = {
    (640, 360): ResolutionSemanticLabel("360p widescreen", "360p widescreen"),
    (480, 270): ResolutionSemanticLabel("270p", "270p"),
    (480, 360): ResolutionSemanticLabel("360p-class", "360p-class"),
    (640, 480): ResolutionSemanticLabel("480p-class", "480p-class"),
    (720, 480): ResolutionSemanticLabel("SD widescreen", "SD widescreen"),
    (1280, 720): ResolutionSemanticLabel("720p", "HD / 720p"),
    (1920, 1080): ResolutionSemanticLabel("1080p", "Full HD / 1080p"),
    (2560, 1440): ResolutionSemanticLabel("1440p", "QHD / 1440p"),
    (3840, 2160): ResolutionSemanticLabel("4K UHD", "4K UHD"),
    (7680, 4320): ResolutionSemanticLabel("8K UHD", "8K UHD"),
}


