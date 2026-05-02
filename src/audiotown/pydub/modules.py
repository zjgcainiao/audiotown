from dataclasses import dataclass

@dataclass(frozen=True)
class WavData:
    """
    A modern container for raw audio data and its properties.
    Replaces the legacy namedtuple from pydub.
    """
    audio_format: int
    channels: int
    sample_rate: int
    bits_per_sample: int
    raw_data: bytes

    @property
    def sample_width(self) -> int:
        """Calculate sample width in bytes (e.g., 16-bit = 2 bytes)."""
        return self.bits_per_sample // 8

    @property
    def frame_width(self) -> int:
        """Total bytes per multi-channel sample frame."""
        return self.channels * self.sample_width