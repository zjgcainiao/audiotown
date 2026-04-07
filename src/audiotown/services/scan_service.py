import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Iterable, Generator, List, Callable
from audiotown.consts.folder_stats import FolderStats
from audiotown.logger import logger, SessionLogger
from audiotown.consts import FolderStats, AppConfig, AudioFormat
from .probe_service import ProbeService
from audiotown.consts.ffmpeg_config import FFmpegConfig

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
            if file.suffix.lower() in target_suffixes:
                yield file


    def get_folder_stats(
        self,
        folder_path: Path,
        # ffprobe_path: str,
        files: Optional[List[Path]] = None,
        max_workers: int = AppConfig().MAX_WORKERS,
        # progress_callback=None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> FolderStats:
        """Gathers technical and metadata stats for a folder."""

        stats = FolderStats(folder_path=folder_path)

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
                executor.submit(self.probe_service.probe_file, f, ): f for f in all_files
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
