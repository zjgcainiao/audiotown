from dataclasses import dataclass, field
from typing import Optional
from .lang_map import LANGUAGE_MAP
from .audio_codec import AudioCodec
@dataclass(slots=True)
class AudioStreamSpec:
    codec_name: str | None
    sample_rate: int | None
    channels: int | None
    bit_rate: int | None
    bits_per_sample: int | None
    # newly added 2024-04-01
    is_default: bool = field(default=False)
    language: Optional[str] = field(default=None)
    stream_index: Optional[int] = field(default=None)


    @property
    def normalized_language(self) -> str | None:
        if not self.language:
            return None

        v = self.language.strip().lower()
        return LANGUAGE_MAP.get(v, v)
    
    @property
    def is_apple_ready(self) -> bool:
        if self.codec_name in [AudioCodec.AAC.value]:
         return True
        return False