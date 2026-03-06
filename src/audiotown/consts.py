from __future__ import annotations
import click
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, List, Any, cast,Set
from collections import Counter, defaultdict
from functools import partial
from audiotown.utils import to_int, div_blocks
from audiotown.logger import SessionLogger



class BitrateTier(str, Enum):
    HIGH = "320k"
    MEDIUM = "256k"
    LOW = "128k"

    @classmethod
    def get_value(cls, key: str) -> str:
        # Allows you to look up "high" and get "320k" safely
        return cls[key.upper()].value

    @classmethod
    def from_str(cls, label: str):
        """Safely find a tier by string, case-insensitive."""
        try:
            return cls[label.upper()]
        except (KeyError, AttributeError):
            return None  # Or return cls.MEDIUM as a safe fallback

    @classmethod
    def supported_bitrates(cls) -> set[str]:
        # Allows you to look up "high" and get "320k" safely

        a_set = {member.value for member in cls}
        return a_set


@dataclass(slots=True)
class TypeSummary:
    count: int = 0
    size_bytes: int = 0


@dataclass(frozen=True, slots=True)
class AudioStream:
    streams: List[Dict[str, Any]] = field(default_factory=list)
    format: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_ffprobe_json(cls, data: Dict[str, Any]) -> "AudioStream":
        """
        Safely extracts 'streams' and 'format' from the raw ffprobe JSON.
        """
        # We use .get() to avoid KeyErrors if ffprobe fails to find a stream
        streams = data.get("streams", [])
        format_info = data.get("format", {})
        return cls(streams=streams, format=format_info)


class AudioFamily(str, Enum):
    LOSSLESS = "lossless"
    LOSSY = "lossy"
    UNKNOWN = "unknown"


class QualityTier(str, Enum):
    LOSSLESS_HIRES = "lossless_hires"
    LOSSLESS_CD = "lossless_cd"
    LOSSLESS_OTHER = "lossless_other"

    LOSSY_HIGH = "lossy_high"
    LOSSY_STANDARD = "lossy_standard"
    LOSSY_LOW = "lossy_low"
    LOSSY_UNKNOWN = "lossy_unknown"
    UNKNOWN = "unknown"


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
        self, ext: str, codec_name: str, encoder: str, is_lossy: bool, description: str
    ):
        self.ext = ext
        self.codec_name = (
            codec_name  # matching `codec_name` from ffprobe -of json output
        )
        self.encoder = encoder  # Use this for the '-c:a' flag in FFmpeg
        self.is_lossy = is_lossy
        self.description = description

    @classmethod
    def from_suffix(cls, suffix: str) -> AudioFormat | None:
        """Find the default format for a given suffix (e.g. .m4a -> ALAC)."""
        suffix = suffix.lower()
        for member in cls:
            if member.ext == suffix:
                return member
        return None

    @classmethod
    def from_codec(cls, codec_name: str) -> Optional[AudioFormat]:
        """Find the default format based on a codec string."""
        for member in cls:
            if member.codec_name == codec_name.lower():
                return member
        return None

    @classmethod
    def is_supported(cls, suffix: str):
        if suffix and suffix.strip() and suffix in {member.ext for member in cls}:
            return True
        return False

    @classmethod
    def supported_extensions(cls) -> set[str]:
        """Returns all unique extensions we care about for scanning."""
        return {member.ext for member in cls}

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



# --- FFmpegConfig ---
@dataclass(frozen=True)
class FFmpegConfig:
    ffmpeg_path: str
    ffprobe_path: str

@dataclass(slots=True)
class AudioRecord:
    file_path: Path
    # common technical fields
    audio_format: AudioFormat  # includes ext, and codec
    bitrate_bps: Optional[int]
    sample_rate_hz: Optional[int]
    bits_per_sample: Optional[int]
    channels: Optional[int]
    size_bytes: int
    duration_sec: Optional[float]

    # common tags (what you aggregate on)
    year: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    title: Optional[str]
    genre: Optional[str]

    # status
    readable: bool = field(default=True)
    error: Optional[str] = ""
    fingerprint: Optional[str] = " _ "  # Calculated at creation

    # default
    has_embedded_artwork: bool = field(default=False)

    @property
    def custom_fingerprint(self) -> Optional[str]:
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
        return int(self.bitrate_bps) / 1000 if self.bitrate_bps else 0

    @property
    def sample_rate_khz(self) -> Optional[float]:
        return int(self.sample_rate_hz) / 1000 if self.sample_rate_hz else 0

    def family(self) -> AudioFamily:
        if not self.readable:
            return AudioFamily.UNKNOWN

        if not self.audio_format.is_lossy:
            return AudioFamily.LOSSLESS
        if self.audio_format.is_lossy:
            return AudioFamily.LOSSY
        # containers can confuse people; codec_name should be a stream codec,
        # but keep a safe fallback:
        return AudioFamily.UNKNOWN

    def is_pcm(self) -> bool:
        return self.audio_format.is_pcm

    def is_lossless(self) -> bool:
        return self.audio_format.is_lossless

    def is_lossy(self) -> bool:
        return self.audio_format.is_lossy

    def is_hires_lossless(self) -> bool:
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
        if self.audio_format.is_lossy:
            return False
        bits = self.bits_per_sample
        sr = self.sample_rate_hz
        return bits == 16 and (sr in (44100, 48000) if sr is not None else False)

    def lossy_bitrate_band(self) -> QualityTier:
        """
        Simple, conservative tiering.
        You can refine per-codec thresholds later (Opus vs MP3 vs AAC).
        """
        if not self.audio_format.is_lossy:
            return QualityTier.UNKNOWN

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
        if not self.readable:
            return QualityTier.UNKNOWN

        fam = self.family()
        if fam == AudioFamily.LOSSLESS:
            if self.is_hires_lossless():
                return QualityTier.LOSSLESS_HIRES
            if self.is_cd_lossless():
                return QualityTier.LOSSLESS_CD
            return QualityTier.LOSSLESS_OTHER

        if fam == AudioFamily.LOSSY:
            return self.lossy_bitrate_band()

        return QualityTier.UNKNOWN

    def is_storage_inefficient(self) -> bool:
        """
        Optional: flag “big-for-what-it-is”.
        Example heuristics:
          - 32-bit float PCM for a music library (not wrong, but huge)
          - very high sample rates (192k) in PCM could be huge too
        """
        if self.is_lossy():
            return False
        bits = self.bits_per_sample or 0
        if self.is_pcm() and bits > 24:
            return True
        if self.is_pcm() and self.sample_rate_hz or 0 > 192 * 1000:
            return True
        return False


# ---------------------------
# FolderStats
# ---------------------------
@dataclass(slots=True)
class FolderStats:
    # folder:
    # folder: Path

    # records
    records: List[AudioRecord] = field(default_factory=list)

    # summary
    total_files: int = 0
    total_bytes: int = 0
    total_duration_sec: float = 0.0
    bloated_files: int = 0
    readable_files: int = 0

    # per-ext summary
    # types: Dict[str, TypeSummary] = field(default_factory=dict)
    missing_artist: int = 0
    missing_album: int = 0
    missing_title: int = 0

    # lossy bitrate bands
    lossy_band_counts: Counter[str] = field(
        default_factory=Counter
    )  # high/standard/low/unknown
    lossy_band_bytes: defaultdict[str, int] = field(
        default_factory=partial(defaultdict, int)
    )

    #
    by_readable: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    by_bloated: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    by_ext: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    by_codec: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    by_family: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    by_tier: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )

    # tag aggregation
    artists: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    albums: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    genres: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    years: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )

    # duplicates by `artist_title`
    fingerprints: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    def _bump(self, table: defaultdict[str, TypeSummary], key: str, size: int) -> None:
        ts = table[key]
        ts.count += 1
        ts.size_bytes += size

    def add(self, rec: AudioRecord) -> None:
        """Single source of truth: updates everything consistently."""

        self.records.append(rec)
        if rec.duration_sec:
            self.total_duration_sec += float(rec.duration_sec)
        
        size = rec.size_bytes
        self.total_files += 1
        self.total_bytes += rec.size_bytes

        # self.bytes_by_ext[rec.audio_format.ext] += rec.size_bytes
        self._bump(self.by_ext, rec.audio_format.ext, size)
        self._bump(self.by_codec, rec.audio_format.codec_name, size)
        self._bump(self.by_family, rec.family(), size)
        self._bump(self.by_tier, rec.quality_tier(), size)
        # e = self.by_ext[rec.audio_format.ext]
        # if e:
        #     e.count += 1
        #     e.size_bytes += rec.size_bytes

        # c = self.by_codec[rec.audio_format.codec_name]
        # if c:
        #     c.count += 1
        #     c.size_bytes += rec.size_bytes

        # f = self.by_family[rec.family()]
        # if f:
        #     f.count += 1
        #     f.size_bytes += rec.size_bytes

        # qt = self.by_tier[rec.quality_tier()]
        # if qt:
        #     qt.count += 1
        #     qt.size_bytes += rec.size_bytes

        # health
        if rec.readable:
            self.readable_files += 1
            self._bump(self.by_readable, "readable", size)
            # self.by_readable["readable"].count += 1
            # self.by_readable["readable"].size_bytes += rec.size_bytes
        else:
            self._bump(self.by_readable, "unreadable_or_errors", size)
            # self.by_readable["unreadable_or_contain_errors"].count += 1
            # self.by_readable["unreadable_or_contain_errors"].size_bytes += rec.size_bytes

        if rec.is_storage_inefficient():
            self.bloated_files += 1
            self._bump(self.by_bloated, "bloated", size)

            # self.by_belated["bloated"].count += 1
            # self.by_belated["bloated"].size_bytes += rec.size_bytes

        # tags -> counters (only count non-empty)
        if rec.artist:
            if rec.artist == AudioFamily.UNKNOWN.value:
                self.missing_artist +=1
            self.artists[rec.artist].count += 1
            self.artists[rec.artist].size_bytes += rec.size_bytes

        if rec.album:
            self.albums[rec.album].count += 1
            self.albums[rec.album].size_bytes += rec.size_bytes
        if rec.genre:
            self.genres[rec.genre].count += 1
            self.genres[rec.genre].size_bytes += rec.size_bytes
        if rec.year and to_int(rec.year) > 1900:
            self.years[rec.year].count += 1
            self.years[rec.year].size_bytes += rec.size_bytes

        # duplicate fingerprint
        fp = rec.fingerprint
        if fp:
            self.fingerprints[fp].count += 1
            self.fingerprints[fp].size_bytes += rec.size_bytes


import json


class AudiotownEncoder(json.JSONEncoder):
    def default(self, o):
        # If the object is a Path (PosixPath or WindowsPath), turn it into a string
        if isinstance(o, Path):
            return str(o)
        if isinstance(o, AudioFormat):
            return {
                "ext": o.ext,
                "codec_name": o.codec_name,
                "encoder": o.encoder,
                "is_lossy": o.is_lossy,
                "description": o.description,
            }
        # Otherwise, let the standard encoder handle it
        return super().default(o)

@dataclass(frozen=True)  # Frozen makes it immutable/read-only (Production Best Practice)
class AppConfig:
    import audiotown
    ff_config: Optional[FFmpegConfig] = None
    version: str = field(default=audiotown.__version__)
    bitrate_tiers : Set[str]= field(default_factory=BitrateTier.supported_bitrates)
    divs_lvl1: str = field(default=div_blocks(10, "= "))
    divs_lvl2: str = field(default=div_blocks(5, "- "))
    supported_extensions: Set[str] = field(default_factory=AudioFormat.supported_extensions)


@dataclass
class AppContext:
    app_config: AppConfig = field(default_factory=AppConfig)
    start_time: float = 0
    run_time: float = 0

    ff_config: Optional[FFmpegConfig] = None

    logger: Optional[SessionLogger] = None
    @classmethod
    def get_app_ctx(cls, ctx: click.Context) -> AppContext:
        # We use cast because Click types ctx.obj as Any
        return cast(AppContext, ctx.obj)
    @classmethod
    def ensure_app_ctx(cls, ctx: click.Context) -> AppContext:
        if ctx.obj is None:
            ctx.obj = AppContext(start_time=0.0, run_time=0,
                                 app_config=AppConfig(), ff_config=None, logger=SessionLogger())
        return cls.get_app_ctx(ctx)
