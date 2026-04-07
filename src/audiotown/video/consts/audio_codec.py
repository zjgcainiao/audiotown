
from enum import StrEnum

class AudioCodec(StrEnum):
    AAC = "aac"
    ALAC = "alac"
    MP3 = "mp3"
    OPUS = "opus"
    PCM_S16LE = "pcm_s16le"
    PCM_S24LE = "pcm_s24le"
    FLAC = "flac"
    
    @property
    def is_lossy(self) -> bool:
        return self in {self.AAC, self.MP3, self.OPUS}

    @property
    def is_lossless(self) -> bool:
        return not self.is_lossy