from dataclasses import dataclass

from .audio.audio_folder_stats import AudioFolderStats
from .video.video_folder_stats import VideoFolderStats


@dataclass(slots=True)
class MediaFolderStats:
    audio_folder_stats: AudioFolderStats | None = None
    video_folder_stats: VideoFolderStats | None = None


    @property
    def total_files(self) -> int:
        total = 0
        if self.audio_folder_stats is not None:
            total += self.audio_folder_stats.total_files
        if self.video_folder_stats is not None:
            total += self.video_folder_stats.total_videos
        return total

    @property
    def total_size_bytes(self) -> int:
        t_bytes = 0
        if self.audio_folder_stats is not None:
            t_bytes += self.audio_folder_stats.total_size_bytes
        if self.video_folder_stats is not None:
            t_bytes += self.video_folder_stats.total_size_bytes
        return t_bytes
    
    @property
    def folder_path(self):
        path1 = self.audio_folder_stats.folder_path if self.audio_folder_stats is not None else None
        path2 = self.video_folder_stats.folder_path if self.video_folder_stats is not None else None

        if path1 is None or path2 is None:
            return None
        elif path1 == path2:
            return path1
        else:
            return None