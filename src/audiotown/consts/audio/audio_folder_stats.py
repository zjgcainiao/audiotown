

import unicodedata
import re
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
from functools import partial
from audiotown.consts.audio import audio_format
from audiotown.utils import  extract_year_from_str, sanitize_metadata
from .audio_record import AudioRecord
from .audio_family import AudioFamily
from ..basics.type_summary import TypeSummary
from .duplicate_group import DuplicateGroup
from .audio_readable import AudioReadable



@dataclass(slots=True)
class AudioFolderStats:
    """
    """
    folder_path: Path | None = None 
    # records
    records: list[AudioRecord] = field(default_factory=list)
    # summary
    total_files: int = 0
    total_size_bytes: int = 0
    total_duration_sec: float = field(default=0.0)
    total_readable: int = 0
    bloated_files: int = 0

    missing_artist: int = 0
    missing_album: int = 0
    missing_title: int = 0

    by_lossy_band: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
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
    by_artist: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    by_album: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    by_genre: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )
    by_year: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )

    by_has_embedded_artwork: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary)
    )

    # duplicates by `artist_title`
    by_fingerprint: defaultdict[str, DuplicateGroup] = field(
        default_factory=partial(defaultdict, DuplicateGroup)
    )

    # new field 2026-04-14
    by_channels: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary))
    
    by_detected_language: defaultdict[str, TypeSummary] = field(
        default_factory=partial(defaultdict, TypeSummary))
    
    

    def add(self, rec: AudioRecord|None) -> None:
        """
            Single source of truth: add a new audio record when scanning the folder. by the completion of the scan,
            AudioFolderStats will contain the complete list of audio records. 
        """
        if rec is None:
            return None
        
        self.total_files += 1
        size = rec.size_bytes
        self.records.append(rec)
        if rec.is_readable:
            self.total_readable += 1
            self._bump(self.by_readable, AudioReadable.READABLE, size)

        else:
            self._bump(self.by_readable, AudioReadable.UNREADABLE, size)
        
        if size is None or rec.duration_sec is None:
            return 
        if rec.duration_sec:
            self.total_duration_sec += float(rec.duration_sec)
        
        self.total_size_bytes += rec.size_bytes if rec.size_bytes is not None else 0
        if rec.audio_format is not None:
            for table, key in (
                (self.by_ext, rec.audio_format.ext),
                (self.by_codec, rec.audio_format.codec_name),
                (self.by_family, rec.family().value),
                (self.by_tier,  rec.quality_tier().value),
                (self.by_lossy_band, rec.lossy_bitrate_band().value if rec.lossy_bitrate_band() is not None else "non lossy"),
                (self.by_channels, str(rec.channels)),
                (self.by_genre, str(rec.genre)),
                (self.by_detected_language, rec.detected_primary_language_name),
            ):
                self._bump(table, key, size)


        if rec.is_storage_inefficient():
            self.bloated_files += 1
            self._bump(self.by_bloated, "bloated", size)

        # tags -> counters (only count non-empty)
        if not rec.title:
            self.missing_title += 1
        if rec.artist:
            if rec.artist.casefold() == AudioFamily.UNKNOWN.value:
                self.missing_artist += 1
            else:
                self._bump(self.by_artist, rec.artist, size)
        else:
            self.missing_artist += 1

        if not rec.album:
            self.missing_album += 1
        else:
            self._bump(self.by_album, rec.album, size)
        # if rec.genre:
        #     self._bump(self.by_genre, rec.genre, size)

        extracted_year = extract_year_from_str(rec.year or "")
        if extracted_year:
            self._bump(self.by_year, str(extracted_year), size)

        if rec.has_embedded_artwork:
            self._bump(self.by_has_embedded_artwork, "has_embedded_artwork", size)

        # duplicate fingerprint
        fp = rec.fingerprint
        if fp is not None:
            meta_key = self._normalize_key(rec.fingerprint) if rec.fingerprint else ""
            meta_key = sanitize_metadata(meta_key)
            # e.g., "01. Hotel California.mp3" -> "01 hotel california"
            name_key = self._normalize_key(rec.file_path.stem)
            name_key = sanitize_metadata(meta_key)
            primary_key = meta_key if meta_key and len(meta_key) > 3 else name_key
            # refined_fp = self._normalize_key(fp)
            self._bump2(self.by_fingerprint, primary_key, size, rec)

    def _bump(self, table: defaultdict[str, TypeSummary], key: str, size: int | None) -> None:
        ts = table[key]
        ts.count += 1
        ts.size_bytes += size if size is not None else 0

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
        dg.size_bytes += audio_record.size_bytes if audio_record.size_bytes is not None else 0
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
        self, audio_records: list[AudioRecord] = list()
    ) -> list[DuplicateGroup]:
        # We use a set of keys to avoid double-counting the same file
        buckets: defaultdict[str, list[AudioRecord]] = defaultdict(list)
        if not audio_records:
            audio_records = self.records
        for rec in audio_records:
            if rec.is_readable is False or rec.audio_format is None:
                continue
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
        results: list[DuplicateGroup] = []
        for key, records in buckets.items():
            if len(records) > 1:
                sorted_recs = sorted(
                    records,
                    key=lambda x: (
                        not x.audio_format.is_lossless if x.audio_format is not None else False,
                        -(x.bitrate_bps or 0),
                    ),
                )
                results.append(DuplicateGroup(key=key, records=sorted_recs))
        return results
