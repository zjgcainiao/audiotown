
from __future__ import annotations
from enum import Enum, StrEnum
from typing import Optional

class AudioFormat(Enum):
    # Member = (extension, codec_name, encoder, is_lossy, description)
    # --- LOSSLESS ---
    FLAC = (".flac", "flac", "flac", False, "Free Lossless Audio Codec")
    ALAC = (".m4a", "alac", "alac", False, "Apple Lossless")
    WAV = (".wav", "pcm_s16le", "pcm_s16le", False, "WAV 16-bit")
    WAV24 = (".wav", "pcm_s24le", "pcm_s24le", False, "WAV 24-bit")

    # --- LOSSY ---
    AAC = (".m4a", "aac", "aac", True, "Advanced Audio Coding")
    M4B = (".m4b", "aac", "aac", True, "MPEG-4 Audiobook")
    MP3 = (".mp3", "mp3", "libmp3lame", True, "MP3 Audio (LAME)")
    OPUS = (".opus", "opus", "libopus", True, "Opus Interactive Audio")
    VORBIS = (".ogg", "vorbis", "libvorbis", True, "Ogg Vorbis")
    WMA = (".wma", "wmav2", "wmav2", True, "Windows Media Audio")

    # requires 4 arguments
    def __init__(
        self, 
        ext: str, 
        codec_name: str, 
        encoder: str, 
        is_lossy: bool, 
        description: str
    ):
        # self.value = ext
        self.ext = ext
        self.codec_name = codec_name
        self.encoder = encoder  # Use this for the '-c:a' flag in FFmpeg
        self.is_lossy = is_lossy
        self.description = description

    @classmethod
    def from_suffix(cls, suffix: str) -> AudioFormat | None:
        """Find the default format for a given suffix (e.g. .m4a -> ALAC)."""
        suffix = suffix.strip().lower()
        for member in cls:
            if member.ext == suffix:
                return member
        return None

    @classmethod
    def from_codec(cls, codec_name: str) -> Optional[AudioFormat]:
        """Find the default format based on a codec string."""
        codec_name = codec_name.strip().lower()
        for member in cls:
            if member.codec_name == codec_name:
                return member
        return None

    @classmethod
    def is_supported(cls, suffix: str| None):
        if not suffix:
            return False
        return suffix.strip().lower() in {member.ext for member in cls}

    @classmethod
    def supported_extensions(cls) -> set[str]:
        """Returns all unique extensions we care about for scanning."""
        return {member.ext for member in cls}
    
    @classmethod
    def supported_codecs(cls) -> set[str]:
        """Returns all unique extensions we care about for scanning."""
        return {member.codec_name for member in cls}

    @classmethod
    def codec_choices(cls) -> list[str]:
        return [cls.ALAC.codec_name, cls.AAC.codec_name]

    @property
    def is_pcm(self) -> bool:
        """Checks if the codec is a Pulse Code Modulation (Raw) format."""
        return self.codec_name.startswith("pcm_")

    @property
    def is_lossless(self) -> bool:
        """
        Calculates lossless status.
        A format is lossless if we marked it False OR if it's PCM.
        """
        return not self.is_lossy or self.is_pcm
