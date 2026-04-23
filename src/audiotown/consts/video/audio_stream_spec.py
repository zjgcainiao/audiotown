from dataclasses import dataclass, field
from typing import Optional, Any
from audiotown.utils import safe_cast
from audiotown.consts.lang.lang_map import LANGUAGE_MAP
from .audio_codec import AudioCodec


@dataclass(slots=True)
class AudioStreamSpec:
    codec_name: str | None
    sample_rate: int | None
    channels: int | None
    bit_rate: int | None
    bits_per_sample: int | None

    # new fields
    sample_fmt: str| None
    channel_layout: str | None
    dmix_mode: int | None
    profile: int | None
    codec_tag_string : str | None

    raw_tags: dict[str, Any] | None  = None  # <--- The "Trash Can" for this specific stream

    # newly added 2024-04-01
    is_default: bool = field(default=False)
    lang: Optional[str] = field(default=None)
    stream_index: Optional[int] = field(default=None)


    @property
    def normalized_language(self) -> str | None:
        if not self.lang:
            return None

        v = self.lang.strip().lower()
        return LANGUAGE_MAP.get(v, v)
    
    @property
    def is_apple_ready(self) -> bool:
        if self.codec_name in [AudioCodec.AAC.value]:
         return True
        return False
    
    @property
    def is_stereo_channel(self) -> bool:
       channels = safe_cast(self.channels, int)
       if channels is not None and channels ==2:
          return True
       else:
          return False
       
    
    @property
    def is_drm_protected(self):
        if self.codec_tag_string:
            if "drm" in self.codec_tag_string.lower():
                return True
        return False