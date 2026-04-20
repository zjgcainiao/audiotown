from dataclasses import dataclass, field
from typing import Optional, Any
from audiotown.consts.lang.lang_map import LANGUAGE_MAP

@dataclass(slots=True)
class SubtitleStreamSpec:
    
    stream_index: Optional[int] = field(default=None)
    codec_name: str | None = None
    lang: str | None = None
    is_default: bool = False
    is_forced: bool = False
    title: str | None = None
    raw_tags: dict[str, Any] | None= None 

    
    @property
    def is_mp4_text_compatible(self) -> bool:
        if not self.codec_name:
            return False
        return self.codec_name.strip().lower() in {"subrip", "srt", "ass", "ssa", "webvtt"}

    @property
    def normalized_language(self) -> str | None:
        if not self.lang:
            return None

        v = self.lang.strip().lower()
        return LANGUAGE_MAP.get(v, v)
