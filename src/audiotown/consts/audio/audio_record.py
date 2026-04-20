
from dataclasses import dataclass, field
from pathlib import Path
from token import OP
from typing import Optional, Any
from functools import cached_property
from audiotown.utils import safe_cast
from sympy import false
from .audio_family import AudioFamily
from .audio_format import AudioFormat
from .quality_tier import QualityTier
from audiotown.consts.basics.attached_pic_spec import AttachedPicSpec
from audiotown.consts.lang.detected_language import DetectedLanguage
@dataclass(slots=True)
class AudioRecord:
    file_path: Path
    # technical fields
    audio_format: Optional[AudioFormat] = None

    # common tags (what you aggregate on)
    year: str | None  = None
    artist: str | None  = None
    album: str | None  = None
    title: str | None  = None
    genre: str | None  = None
    track: str | None  = None

    bitrate_bps: Optional[int] = None
    sample_rate_hz: Optional[int] = None
    bits_per_sample: Optional[int] = None
    channels: Optional[int] = None
    size_bytes: Optional[int] = None
    duration_sec: Optional[float] = None

    # status
    is_readable: bool = field(default=True)
    error: str | None  = None
    fingerprint: str | None  = " _ "  # Calculated at creation

    # default
    has_embedded_artwork: bool = field(default=False)

    # new field raw_tags
    channel_layout: str | None = None
    nb_streams: int | None = None
    probe_score: int | None = None
    sample_fmt: str | None = None
    raw_tags: dict[str, Any] | None = None
    attached_pics: list[AttachedPicSpec] = field(default_factory=list)

    @property
    def custom_fingerprint(self) -> str | None :
        """
        Duplicate heuristic:
        - normalized artist + title
        - only returns if both exist
        """
        if not self.artist or not self.title:
            return None
        a = self.artist.casefold()
        t = self.title.casefold()
        # if not a or not t:
        #     return None
        return f"{a}" + "_" + f"{t}"

    @property
    def bitrate_kbps(self) -> Optional[float]:
        if self.bitrate_bps is None:
            return None
    
        return float(self.bitrate_bps)/1000.0 if safe_cast(self.bitrate_bps, float) is not None else None

    @property
    def sample_rate_khz(self) -> Optional[float]:
        if self.sample_rate_hz is None:
            return None
        return self.sample_rate_hz / 1000 
    
    @property 
    def is_stereo_channel(self) -> bool:
        if self.channels is not None and self.channels==2:
            return True
        else:
            return False

    def find_external_cover_art(self, folder_path: Path) -> Optional[Path]:
        valid_names = {"cover", "folder", "front", "album"}
        valid_extensions = {".jpg", ".jpeg", ".png"}
        if not folder_path or not Path(folder_path).is_dir:
            return None
        try:
            for file in folder_path.iterdir():
                if file.is_file():
                    if (
                        file.stem.lower() in valid_names
                        and file.suffix.lower() in valid_extensions
                    ):
                        return file
        except PermissionError:
            return None
        except Exception:
            return None
        return None

    def family(self) -> Optional[AudioFamily]:
        if not self.is_readable:
            return AudioFamily.UNKNOWN
        if self.audio_format is None:
            return AudioFamily.UNKNOWN
        if not self.audio_format.is_lossy:
            return AudioFamily.LOSSLESS
        if self.audio_format.is_lossy:
            return AudioFamily.LOSSY
        # containers can confuse people; codec_name should be a stream codec,
        # but keep a safe fallback:
        return AudioFamily.UNKNOWN

    def is_pcm(self) -> bool:
        if self.audio_format is None:
            return False
        return self.audio_format.is_pcm if self.audio_format is not None else False

    def is_lossless(self) -> bool:
        if self.audio_format is None:
            return False
        return self.audio_format.is_lossless

    def is_lossy(self) -> bool:
        return self.audio_format.is_lossy if self.audio_format is not None else False

    def is_hires_lossless(self) -> bool:
        """ determines if the audio is high resolution lossless
        criteria: 
            - is lossless.
            - need to meet one of the two
                - bit_per_sample>24, or 
                - sample_rate > 48000
        Returns:
            bool: True or False
        """
        if self.audio_format is None:
            return False
        if self.audio_format.is_lossy:
            return False
        bits = self.bits_per_sample
        sr = self.sample_rate_hz
        #  “hi-res” definition: >=24-bit OR >48kHz
        is_high_res: bool = (bits is not None and bits >= 24) or (
            sr is not None and sr > 48000
        )
        return is_high_res

    def is_cd_lossless(self) -> bool:
        """ determines if the audio is high resolution lossless
        criteria: 
            - is lossless.
            - bits_per_sample = 16
            - sample_rate (44.1Khz and 48 Khz)
            - sample_rate > 48000
        Returns:
            bool: True or False
        """
        if self.audio_format is None:
            return False

        if self.audio_format.is_lossy:
            return False
        bits = self.bits_per_sample
        sr = self.sample_rate_hz
        return bits == 16 and (sr in (44100, 48000) if sr is not None else False)

    def lossy_bitrate_band(self) -> Optional[QualityTier]:
        """
        Simple, conservative tiering.
        You can refine per-codec thresholds later (Opus vs MP3 vs AAC).
        """
        if self.audio_format is None:
            return None
        if not self.audio_format.is_lossy:
            return None
        # calc bit_rate
        br = self.bitrate_kbps
        if br is None or br <= 0:
            return QualityTier.LOSSY_UNKNOWN

        # baseline thresholds; tweak as desired
        if br >= 256:
            return QualityTier.LOSSY_HIGH
        if br >= 160:
            return QualityTier.LOSSY_STANDARD
        return QualityTier.LOSSY_LOW

 
    def quality_tier(self) -> QualityTier:
        """
        The one function you call everywhere.
        """
        if not self.is_readable:
            return QualityTier.UNKNOWN
        fam = self.family()
        if fam == AudioFamily.LOSSLESS:
            if self.is_hires_lossless():
                return QualityTier.LOSSLESS_HIRES
            if self.is_cd_lossless():
                return QualityTier.LOSSLESS_CD
            return QualityTier.LOSSLESS_OTHER

        if fam == AudioFamily.LOSSY:
            # return self.lossy_bitrate_band()
            # calc bit_rate
            br = self.bitrate_kbps
            if br is None or br <= 0:
                return QualityTier.LOSSY_UNKNOWN

            # baseline thresholds; tweak as desired
            if br >= 256:
                return QualityTier.LOSSY_HIGH
            if br >= 160:
                return QualityTier.LOSSY_STANDARD
            return QualityTier.LOSSY_LOW

        return QualityTier.UNKNOWN

    def is_storage_inefficient(self) -> bool:
        """
        Optional: flag “big-for-what-it-is” PCM raw sample.
        Example heuristics:
          - 32-bit float PCM for a music library (not wrong, but huge)
          - very high sample rates (192k) in PCM could be huge too
        """
        if self.is_lossy():
            return False
        bits = self.bits_per_sample or 0
        s_rate = self.sample_rate_hz or 0
        if bits is None or s_rate is None:
            return False
        if self.is_pcm() and bits > 24:
            return True
        if self.is_pcm() and s_rate or 0 > 192 * 1000:
            return True
        return False

    def has_attached_pic(self) -> bool:
        if self.attached_pics is not None and len(self.attached_pics) > 0:
            return True

        return False
    

    @property
    def detected_language(self) -> DetectedLanguage:
        """Analyzes combined metadata to detect script and language."""
        # Join components into a single 'fingerprint' string
        tags_str = " ".join(self.raw_tags) if self.raw_tags else ""
        text_to_analyze = f"{self.title} {self.file_path} {tags_str}"
        
        # One-line instantiation
        return DetectedLanguage.from_text(text_to_analyze)

    @property
    def detected_primary_language_name(self) -> str:
        """The user-facing string for the dashboard."""
        return self.detected_language.primary_identity.value.title()