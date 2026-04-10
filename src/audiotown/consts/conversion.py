from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from .audio_format import AudioFormat
from audiotown.utils import make_json_safe
from audiotown.consts.video.video_container import VideoContainer


# -----------------------------
# Conversion Report Structure
# -----------------------------

# for concurrent running. need a task object to hold each job, aka ConversionTask.
@dataclass(slots=True)
class ConversionTask:
    file_path: Path
    target: AudioFormat | VideoContainer
    output_path: Path
    bitrate: Optional[str] = None


@dataclass(slots=True)
class ConversionTaskResult:
    file_path: Path
    output_path: Path
    success: bool = False
    message: str = ""

@dataclass(slots=True)
class ConversionDetail:
    source: str
    destination: str
    status: str  # "SUCCESS" or "FAILED"
    error_message: str | None = None


@dataclass(slots=True)
class ConversionReport:
    """ summary of a conversion job.

    Returns:
        folder_path: the selected folder for job
        total: the total number of files to convert
        sucecess:
        failed:
        details: a list of ConversionDetail
        run_time: 
    """
    folder_path: Path
    start_time: str = field(
        default_factory=lambda: datetime.now().astimezone().isoformat()
    )
    total: int = 0
    success: int = 0
    failed: int = 0
    details: List[ConversionDetail] = field(default_factory=list)
    run_time: Optional[float] = None

    def add_detail(self, detail: ConversionDetail):
        self.details.append(detail)
        self.total += 1
        if detail.status.upper() == "SUCCESS":
            self.success += 1
        else:
            self.failed += 1

    def to_dict(self):
        """Converts the whole tree to a dictionary for JSON exporting."""
        data = asdict(self)
        # data["folder_path"] = str(self.folder_path)
        safe_data = make_json_safe(data)
        return safe_data
        # return asdict(self)
