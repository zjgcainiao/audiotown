from __future__ import annotations
import click
import re
import json
import unicodedata
import os
from enum import Enum
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Tuple, Dict, List, Any, cast, Set
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


@dataclass(slots=True)
class Type2Summary:
    count: int = 0
    size_bytes: int = 0
    files: List[Path] = field(default_factory=list)


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

    # common tags (what you aggregate on)
    year: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    title: Optional[str]
    genre: Optional[str]
    track: Optional[str]

    bitrate_bps: Optional[int] = 0
    sample_rate_hz: Optional[int] = 0
    bits_per_sample: Optional[int] = 0
    channels: Optional[int] = 0
    size_bytes: int = 0
    duration_sec: Optional[float] = 0

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


@dataclass(slots=True)
class DuplicateGroup:
    records: list[AudioRecord] = field(default_factory=list)
    key: str = ""
    count: int = 0
    size_bytes: int = 0

    @property
    def waste_size(self) -> int:
        if len(self.records) < 2:
            return 0
        # 1. Sort by Quality (Lossless first, then High Bitrate)
        # This ensures the 'Best' file is at index 0
        records = self.records
        sorted_recs = sorted(
            self.records,
            key=lambda x: (not x.audio_format.is_lossless, -to_int(x.bitrate_bps)),
        )

        # 2. Sum up every file EXCEPT the first one (the keeper)
        return sum(rec.size_bytes for rec in sorted_recs[1:])


# ---------------------------
# FolderStats
# ---------------------------
@dataclass(slots=True)
class FolderStats:
    folder_path: Optional[Path] 
    # records
    records: List[AudioRecord] = field(default_factory=list)

    # summary
    total_files: int = 0
    total_bytes: int = 0
    total_duration_sec: float = 0.0
    bloated_files: int = 0
    readable_files: int = 0

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

    by_has_embedded_artwork: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )

    # duplicates by `artist_title`
    fingerprints: defaultdict[str, DuplicateGroup] = field(
        default_factory=partial(defaultdict, DuplicateGroup)
    )

    def add(self, rec: AudioRecord) -> None:
        """Single source of truth: updates everything consistently."""

        self.records.append(rec)
        if rec.duration_sec:
            self.total_duration_sec += float(rec.duration_sec)

        size = rec.size_bytes
        self.total_files += 1
        self.total_bytes += rec.size_bytes

        for table, key in (
            (self.by_ext, rec.audio_format.ext),
            (self.by_codec, rec.audio_format.codec_name),
            (self.by_family, rec.family()),
            (self.by_tier, rec.quality_tier()),
        ):
            self._bump(table, key, size)

        if rec.readable:
            self.readable_files += 1
            self._bump(self.by_readable, "readable", size)

        else:
            self._bump(self.by_readable, "unreadable_or_errors", size)

        if rec.is_storage_inefficient():
            self.bloated_files += 1
            self._bump(self.by_bloated, "bloated", size)

        # tags -> counters (only count non-empty)
        if not rec.title:
            self.missing_title += 1
        if rec.artist:
            if rec.artist == AudioFamily.UNKNOWN.value:
                self.missing_artist += 1
            else:
                self._bump(self.artists, rec.artist, size)

        # if rec.album:
        if not rec.album:
            self.missing_album += 1
        else:
            self._bump(self.albums, rec.album, size)
        if rec.genre:
            self._bump(self.genres, rec.genre, size)

        if rec.year and to_int(rec.year) > 1900:
            self._bump(self.years, rec.year, size)

        if rec.has_embedded_artwork:
            self._bump(self.by_has_embedded_artwork, "has_embedded_artwork", size)

        # duplicate fingerprint
        fp = rec.fingerprint
        if fp:
            meta_key = self._normalize_key(rec.fingerprint) if rec.fingerprint else None

            # Key B: The Filename (Stem only, ignore extension)
            # e.g., "01. Hotel California.mp3" -> "01 hotel california"
            name_key = self._normalize_key(rec.file_path.stem)

            # We "Bucket" it under both. If the metadata is missing, name_key saves us.
            # If the filename is "Track 01" but metadata is correct, meta_key saves us.
            primary_key = meta_key if meta_key and len(meta_key) > 3 else name_key
            # refined_fp = self._normalize_key(fp)
            self._bump2(self.fingerprints, primary_key, size, rec)

    def _bump(self, table: defaultdict[str, TypeSummary], key: str, size: int) -> None:
        ts = table[key]
        ts.count += 1
        ts.size_bytes += size

    def _bump2(
        self,
        table: defaultdict[str, DuplicateGroup],
        key: str,
        size: int,
        audio_record: AudioRecord,
    ) -> None:
        dg = table[key]
        dg.key = key
        dg.count += 1
        # dg.size_bytes += size
        dg.size_bytes += audio_record.size_bytes
        dg.records.append(audio_record)
        # recs = table[key].records
        # if len(recs) > 1:
        #     sorted_recs = sorted(
        #         recs,
        #         key=lambda x: (not x.audio_format.is_lossless, -(x.bitrate_bps or 0))
        #     )
        #     table[key].records = sorted_recs

    def _normalize_key(self, s: str) -> str:
        _ws = re.compile(r"\s+")
        _keep = re.compile(
            r"[^\w\s]", flags=re.UNICODE
        )  # remove punctuation; keep letters/digits/underscore
        s = unicodedata.normalize("NFKC", s)
        s = s.casefold()
        s = s.replace("_", " ")
        s = _keep.sub(" ", s)  # turn punctuation into spaces
        s = _ws.sub(" ", s).strip()
        return s

    def find_duplicates(
        self, audio_records: List[AudioRecord] = list()
    ) -> List[DuplicateGroup]:
        # We use a set of keys to avoid double-counting the same file
        buckets: defaultdict[str, list[AudioRecord]] = defaultdict(list)
        if not audio_records:
            audio_records = self.records
        for rec in audio_records:
            # Key A: The Metadata Fingerprint (Artist - Title)
            meta_key = self._normalize_key(rec.fingerprint) if rec.fingerprint else None

            # Key B: The Filename (Stem only, ignore extension)
            # e.g., "01. Hotel California.mp3" -> "01 hotel california"
            name_key = self._normalize_key(rec.file_path.stem)

            # We "Bucket" it under both. If the metadata is missing, name_key saves us.
            # If the filename is "Track 01" but metadata is correct, meta_key saves us.
            primary_key = meta_key if meta_key and len(meta_key) > 3 else name_key
            buckets[primary_key].append(rec)
        # 2. Filter out buckets with only 1 file (those aren't duplicates)
        results: List[DuplicateGroup] = []
        for key, records in buckets.items():
            if len(records) > 1:
                sorted_recs = sorted(
                    records,
                    key=lambda x: (
                        not x.audio_format.is_lossless,
                        -(x.bitrate_bps or 0),
                    ),
                )
                results.append(DuplicateGroup(key=key, records=sorted_recs))
        return results


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


import audiotown
import platform


@dataclass(frozen=True, slots=True)
class MetaContent:
    Software: str = "Audiotown"
    Version: str = field(default=str(audiotown.__version__))
    Timestamp: str = field(default_factory=datetime.now().isoformat)
    User: str = field(default_factory=lambda: Path.home().name)
    Python: str = field(default_factory=platform.python_version)
    OS: str = field(default_factory=platform.platform)

    def to_text(self) -> str:
        """
        Dynamically generates the meta text by iterating over
        the dataclass fields.
        """
        # 1. Convert the dataclass to a dictionary
        data = asdict(self)

        # 2. Create the lines using a List Comprehension
        # We capitalize the key and add a colon for that 'Apple' look
        lines = [
            f"{key.replace('_', ' ').title():<12}: {value}"
            for key, value in data.items()
        ]

        # 3. Join them into one big string
        return "\n".join(lines)


# Frozen makes it immutable/read-only
@dataclass(frozen=True)
class AppConfig:
    import audiotown

    ff_config: Optional[FFmpegConfig] = None
    version: str = field(default=audiotown.__version__)
    supported_bitrates: Set[str] = field(default_factory=BitrateTier.supported_bitrates)
    divs_lvl1: str = field(default=div_blocks(10, "= "))
    divs_lvl2: str = field(default=div_blocks(5, "- "))
    supported_extensions: Set[str] = field(
        default_factory=AudioFormat.supported_extensions
    )
    MAX_WORKERS: int = field(default_factory=lambda: min(32, (os.cpu_count() or 4) * 2))
    EXPORT_DIR_NAME = f"audiotown_convert"
    READABLE: str = "readable"
    UNREADABLE: str = "unreadable_or_errors"
    BLOATED: str = "bloated"
    TOPS: int = 5  # show top 5 artists,
    MEGA_BYTES: int = 1024**2
    GIGA_BYTES: int = 1024**3
    SECS_PER_DAY: int = 24 * 60 * 60
    SECS_PER_HOUR: int = 60 * 60


@dataclass(slots=True)
class AppContext:
    app_config: AppConfig = field(default_factory=AppConfig)
    start_time: float = 0
    run_time: float = 0
    ff_config: Optional[FFmpegConfig] = None
    logger: SessionLogger = field(default_factory=SessionLogger)
    dry_run: bool = False
    verbose: bool = False
    meta_content: MetaContent = field(default_factory=MetaContent)

    @classmethod
    def get_app_ctx(cls, ctx: click.Context) -> AppContext:
        # We use cast because Click types ctx.obj as Any
        return cast(AppContext, ctx.obj)

    @classmethod
    def ensure_app_ctx(cls, ctx: click.Context) -> AppContext:
        if ctx.obj is None:
            ctx.obj = AppContext(
                start_time=0.0,
                run_time=0,
                app_config=AppConfig(),
                ff_config=None,
                logger=SessionLogger(),
            )
        return cls.get_app_ctx(ctx)


@dataclass(slots=True)
class CmdArgsConfig:
    cmd_name: str
    dry_run: bool = False
    verbose: bool = False
    report_path: Optional[Path] = None
    bit_rate: int = 0
    find_duplicate: bool = False

    def __init__(self, cmd_name: str):
        self.cmd_name = cmd_name
        self.dry_run = False
        self.report_path = None
        self.bit_rate = 0
        self.find_duplicate = False
        if not self.cmd_name:
            raise ValueError(f"Error A cmmd name is requried.")


# -----------------------------
# Conversion Report Structure
# -----------------------------
@dataclass(slots=True)
class ConversionDetail:
    source: str
    destination: str
    status: str  # "SUCCESS" or "FAILED"
    error_message: str | None = None


@dataclass(slots=True)
class ConversionReport:
    start_time: str = field(
        default_factory=lambda: datetime.now().astimezone().isoformat()
    )
    total: int = 0
    success: int = 0
    failed: int = 0
    details: List[ConversionDetail] = field(default_factory=list)

    def add_detail(self, detail: ConversionDetail):
        self.details.append(detail)
        self.total += 1
        if detail.status.upper() == "SUCCESS":
            self.success += 1
        else:
            self.failed += 1

    def to_dict(self):
        """Converts the whole tree to a dictionary for JSON exporting."""
        return asdict(self)



# for concurrent running. need a task object to hold each job, aka ConversionTask.
@dataclass(slots=True)
class ConversionTask:
    file_path: Path
    target: AudioFormat       
    output_path: Path
    app_context: AppContext
    bitrate: str

@dataclass(slots=True)
class ConversionTaskResult:
    file_path: Path
    success: bool = False
    message: str = ""