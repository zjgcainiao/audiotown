from __future__ import annotations
from enum import StrEnum
from .audio_codec import AudioCodec

class AudioEncoder(StrEnum):
    AAC = "aac"
    ALAC = "alac"
    LIBMP3LAME = "libmp3lame"
    LIBOPUS = "libopus"
    FLAC = "flac"
    PCM_S16LE = "pcm_s16le"
    PCM_S24LE = "pcm_s24le"

    @property
    def codec(self) -> AudioCodec:
        _AUDIO_ENCODER_TO_CODEC: dict[AudioEncoder, AudioCodec] = {
            AudioEncoder.AAC: AudioCodec.AAC,
            AudioEncoder.ALAC: AudioCodec.ALAC,
            AudioEncoder.LIBMP3LAME: AudioCodec.MP3,
            AudioEncoder.LIBOPUS: AudioCodec.OPUS,
            AudioEncoder.FLAC: AudioCodec.FLAC,
            AudioEncoder.PCM_S16LE: AudioCodec.PCM_S16LE,
            AudioEncoder.PCM_S24LE: AudioCodec.PCM_S24LE,
        }

        return _AUDIO_ENCODER_TO_CODEC[self]

    @property
    def is_lossy(self) -> bool:
        return self.codec in {
            AudioCodec.AAC,
            AudioCodec.MP3,
            AudioCodec.OPUS,
        }

    @property
    def is_lossless(self) -> bool:
        return not self.is_lossy
    


