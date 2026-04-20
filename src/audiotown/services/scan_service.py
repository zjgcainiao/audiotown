import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Iterable, Generator, List, Callable
from audiotown.consts.video.video_container import VideoContainer
from audiotown.logger import logger, SessionLogger
from audiotown.consts.audio import AudioFolderStats, AudioFormat
from audiotown.consts.video import VideoFolderStats, VideoContainer
from audiotown.consts.app_config import AppConfig
from .probe_service import ProbeService
from audiotown.consts.basics.ffmpeg_config import FFmpegConfig



class ScanService:
    def __init__(self, probe_service: ProbeService, logger:SessionLogger = logger):
        self.probe_service = probe_service
        self.logger = logger
    
    @classmethod
    def from_config(cls, ff_config: FFmpegConfig) -> "ScanService":
        ffprobe_path = ff_config.require_ffprobe()
        return cls(probe_service = ProbeService(ffprobe_path=ffprobe_path))

    def get_audio_files(self,
        directory: Path, supported_formats: Optional[Iterable[AudioFormat]] = None
    ) -> Generator[Path, None, None]:
        """
        Finds all files in a directory matching the supported AudioFormats.
        If 'formats' is provided, it filters specifically for those.
        """
        if directory.is_file():
            # Using the logger we built to keep the UI consistent
            logger.stream(
                "Provided path is a file; scanning the parent directory instead.",
                fg="yellow",
            )
            directory = directory.parent

        target_suffixes = (
            {fmt.ext for fmt in supported_formats}
            if supported_formats
            else AudioFormat.supported_extensions()
        )

        # .rglob is recursive (finds files in subfolders)
        for file in directory.rglob("*"):  
            # Check if the file's suffix (lowercased) is in our allowed set
            # if AudioFormat.is_supported(file.suffix):
            if file.suffix and file.suffix.lower() in target_suffixes:
                yield file


    def get_video_files(self,
        directory: Path, searchable_containers: Optional[Iterable[VideoContainer]] = None
    ) -> Generator[Path, None, None]:
        """
        Finds all files in a directory matching the supported VideoContainers.
        If 'formats' is provided, it filters specifically for those.
        """
        if not directory.exists():
           return None
        if directory.is_file():
            # Using the logger we built to keep the UI consistent
            logger.stream(
                "Provided path is a file; scanning the parent directory instead.",
                fg="yellow",
            )
            directory = directory.parent

        target_suffixes = {container.suffix for container in searchable_containers} if searchable_containers else VideoContainer.supported_suffixes()
        # .rglob is recursive (finds files in subfolders)
        for file in directory.rglob("*"):  
            # Check if the file's suffix (lowercased) is in our allowed set
            # if AudioFormat.is_supported(file.suffix):
            if file.suffix and file.suffix.lower() in target_suffixes:
                yield file

    def get_media_files_by_suffix(self,
        directory: Path, source_suffixes: Iterable[str] | None = None
    ) -> Generator[Path, None, None]:
        """
        Finds files in a directory matching the provided suffixes.
        Decoupled: This doesn't care about 'Audio' vs 'Video', just 'Suffixes'.
        """
        if not directory.exists():
           return # Generators should just 'return' to stop iteration, never return None
        if directory.is_file():
            # Using the logger we built to keep the UI consistent
            logger.stream(
                "Provided path is a file; scanning the parent directory instead.",
                fg="yellow",
            )
            directory = directory.parent
        validated_suffixes = set()
        if source_suffixes is None:
            return # Generators should just 'return' to stop iteration, never return None

        validated_suffixes = {
            f".{s.lstrip('.').lower()}" for s in source_suffixes
        }
        # target_suffixes = {container.suffix for container in searchable_containers} if searchable_containers else VideoContainer.supported_suffixes()
        # .rglob is recursive (finds files in subfolders)
        for file in directory.rglob("*"):  
            # Check if the file's suffix (lowercased) is in our allowed set
            # if AudioFormat.is_supported(file.suffix):
            if file.suffix and file.suffix.lower() in validated_suffixes:
                yield file


    def get_audio_folder_stats(
        self,
        folder_path: Path,
        files: Optional[List[Path]] = None,
        max_workers: int = AppConfig().MAX_WORKERS,
        # progress_callback=None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> AudioFolderStats:
        """Gathers technical and metadata stats for a folder."""

        stats = AudioFolderStats(folder_path=folder_path)

        if files is not None:
            all_files = files
        else: 
            all_files = list(self.get_audio_files(folder_path))
        total = len(all_files)
        # self.logger.regular_log(f'total: {total}....self.probe_service.ffprobe_path: {self.probe_service.ffprobe_path}...',level=logging.INFO)
        # logging.log(msg=f'\n...total: {total}....all_files: {all_files}...',level=logging.ERROR)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 2. Submit all tasks
            futures = {
                executor.submit(self.probe_service.probe_audio, f, ): f for f in all_files
            }
            completed = 0
            # 3. Process as they finish
            for future in as_completed(futures):
                # logging.log(msg=f'\n...total: {total}....stats: {stats}...',level=logging.ERROR) 
                record = future.result()
                if record:
                    # logging.log(msg=f'\n...total: {total}....record: {record}...',level=logging.ERROR) 
                    stats.add(record)
                    # 4. Update the bar immediately
                    # bar.update(1)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
        
        return stats
    
    def get_video_folder_stats(
        self,
        folder_path: Path,
        files: list[Path] | None = None,
        max_workers: int = AppConfig().MAX_WORKERS,
        # progress_callback=None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> VideoFolderStats:
        """
        Scan the folder and return aggregate stats.

        Args:
            progress_callback:
                Optional callback invoked as progress_callback(done, total)
                each time a file finishes processing.
        """

        stats = VideoFolderStats(folder_path=folder_path)

        if files is not None:
            all_videos = files
        else: 
            all_videos = list(self.get_video_files(folder_path))
        total = len(all_videos)
        # self.logger.regular_log(f'total: {total}....self.probe_service.ffprobe_path: {self.probe_service.ffprobe_path}...',level=logging.INFO)
        # logging.log(msg=f'\n...total: {total}....all_files: {all_files}...',level=logging.ERROR)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 2. Submit all tasks
            futures = {
                executor.submit(self.probe_service.probe_video, f, ): f for f in all_videos
            }
            completed = 0
            # 3. Process as they finish
            for future in as_completed(futures):
                # logging.log(msg=f'\n...total: {total}....stats: {stats}...',level=logging.ERROR) 
                record = future.result()
                if record:
                    # logging.log(msg=f'\n...total: {total}....record: {record}...',level=logging.ERROR) 
                    stats.add_video(record)
                    # 4. Update the bar immediately
                    # bar.update(1)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
        
        return stats
