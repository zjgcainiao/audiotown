
import logging
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
from audiotown.utils import safe_cast

from audiotown.consts.basics.type_summary import TypeSummary
from .video_duplicate_group import VideoDuplicateGroup
from .video_record import VideoRecord
from .video_readable import VideoReadable


logger = logging.getLogger(__name__)

@dataclass(slots=True)
class VideoFolderStats:
    """
    save a folder scan of video files into one sumamry object. 
    includes the list of probed video files (VideoRecords).

    """
    folder_path: Path | None = None
    videos: list[VideoRecord]  = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_videos: int = field(default=0)
    total_readable: int = field(default=0)
    total_size_bytes: int = field(default=0)
    total_duration_sec: float = field(default=0.0)
    
    missing_audios: int = 0
    missing_videos: int = 0

    by_suffix: defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    by_container: defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    by_video_codec: defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    by_audio_codec:defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    by_resolution: defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    by_readable: defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    by_apple_compatibility: defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    by_bit_rate: defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    by_bit_depth: defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    by_language: defaultdict[str, TypeSummary] = field(
        default_factory=lambda: defaultdict(TypeSummary)
    )
    # helper function to add into aggregate fields such as `by_readable`, or by_suffix
    def _bump(self, aggregate_field: defaultdict[str, TypeSummary], key: str, size: int | None) -> None:
        """
        A helper funciton that udpates an aggregate field such as `by_readable`.
        Example: {"readable":TypeSummary(size=2048, count=2),"unreadable":TyeSummary(size=1024, count=1)}
        
        Args:
            aggregate_field (defaultdict[str, TypeSummary]): _description_
            key (str): _description_
            size (int | None): _description_
        """
        ts = aggregate_field[key]
        ts.count += 1
        ts.size_bytes += size if size is not None else 0
    
    def add_video(self, video: VideoRecord) -> None:
        if video is None:
            return None
        
        self.total_videos += 1
        size = video.size_bytes

        self.videos.append(video)
        self.errors.append(video.error)

        if video.is_readable:
            self.total_readable += 1
            self._bump(self.by_readable, VideoReadable.READABLE.value, size)
        else:
            self._bump(self.by_readable, VideoReadable.UNREADABLE.value, size)


        if size is None or video.duration_sec is None:
            return
        else:
            self.total_size_bytes += video.size_bytes if video.size_bytes is not None else 0
        if video.duration_sec:
            self.total_duration_sec += float(video.duration_sec)
        
        if not video.has_audio:
            self.missing_audios += 1
        if not video.has_video:
            self.missing_videos += 1

        if video.container_name is not None:
            for aggr_field, key in (
                (self.by_container, video.container_name.muxer),
                (self.by_suffix, video.container_name.suffix),

            ):       
                self._bump(aggr_field, key, size)


        # lets fucking do `by_resolution`, `bit_depth` and `by_video_codec`
        if video.video_stream_count > 0:
            for idx, item in enumerate(video.video_streams):
                resolution = str(item.resolution) # or ""
                video_codec = str(item.codec_name) or ""
                bit_depth = str(item.bit_depth)
                self._bump(self.by_resolution, resolution, size)
                self._bump(self.by_video_codec, video_codec,size)
                self._bump(self.by_bit_depth, bit_depth, size)
        
        if video.audio_stream_count > 0:
            for idx, item in enumerate(video.audio_streams):
                audio_codec = str(item.codec_name)
                self._bump(self.by_audio_codec, audio_codec, size)

        self._bump(self.by_apple_compatibility, video.apple_compatibility.proper(), size)

        self._bump(self.by_bit_rate, str(video.bit_rate), size)

        # add do `by_language`
        if video.languages and len(video.languages) > 0:
            for lang in filter(None, video.languages):
                self._bump(self.by_language, lang, size)
            # for lang in video.languages:
            #     if lang is not None:
            #         self._bump(self.by_language, lang, size)

    