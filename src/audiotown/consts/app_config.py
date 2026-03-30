import os
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Optional, Tuple, Dict, List, Any, cast, Set, DefaultDict
from collections import Counter, defaultdict
from functools import partial
from audiotown.utils import to_int, div_blocks, extract_year_from_str, sanitize_metadata
from .ffmpeg_config import FFmpegConfig
from .birate_tier import BitrateTier
from .audio_format import AudioFormat
import audiotown


# Frozen makes it immutable/read-only
@dataclass(frozen=True)
class AppConfig:
    # ff_config: Optional[FFmpegConfig] = None
    version: str = field(default=audiotown.__version__)
    supported_bitrates: Set[str] = field(default_factory=BitrateTier.supported_bitrates)
    divs_lvl1: str = field(default=div_blocks(10, "= "))
    divs_lvl2: str = field(default=div_blocks(5, "- "))
    supported_extensions: Set[str] = field(
        default_factory=AudioFormat.supported_extensions
    )
    MAX_WORKERS: int = field(default_factory=lambda: min(32, (os.cpu_count() or 4) * 2)-1)
    EXPORT_DIR_NAME = f"audiotown_convert"
    READABLE: str = "readable"
    UNREADABLE: str = "unreadable_or_errors"
    BLOATED: str = "bloated"
    TOPS: int = 5  # show top 5 artists,
    MEGA_BYTES: int = 1024**2
    GIGA_BYTES: int = 1024**3
    SECS_PER_DAY: int = 24 * 60 * 60
    SECS_PER_HOUR: int = 60 * 60