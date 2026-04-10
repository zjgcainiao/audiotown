import json
import platform
import dataclasses
import audiotown
from typing import Tuple
from datetime import datetime
from pathlib import Path
from audiotown.logger import SessionLogger, logger
from audiotown.consts import (
    FolderStats,
    AudiotownEncoder,
    ConversionReport,
    MetaContent,
)
from dataclasses import asdict

def create_report_for_convert(
    report_dir: Path,
    conv_report: ConversionReport,
    logger: SessionLogger,
) -> Tuple[bool, str]:
    try:
        # 1. Ensure the directory exists
        if not report_dir or not report_dir.is_dir():
            logger.stream(
                f" Cannot find {report_dir} or the report path does not exist.",
                err=True,
                fg="yellow",
            )
            return False, "the directory path does not exist."

        # 2. Save JSON
        # logger.stream(f'In `create_report_for_convert, conv_report: {conv_report}\n')
        json_data = json.dumps(
            # conv_report.to_dict(),
            asdict(conv_report),
            indent=4,
            ensure_ascii=False,
            cls=AudiotownEncoder,
        )
        Path(report_dir / "convert.json").write_text(json_data, encoding="utf-8")

        # 3. Save Session Log (The "tee" output)
        Path(report_dir / "run.log").write_text(
            logger.get_full_log(), encoding="utf-8"
        )
        meta_text = MetaContent().to_text()

        # Pathlib writes (Clean & Fast)
        Path(report_dir / "meta.txt").write_text(meta_text, encoding="utf-8")

        return True, ""
    except Exception as e:
        logger.stream(
            f"Error: unexpected error occurred when exporting the report. {e}",
            err=True,
            fg="yellow",
        )
        return False, "Unexpected Error during ffmpeg"


def generate_report_for_stats(
    report_path: Path, stats_folder: Path, stats: FolderStats
) -> bool:
    """
    Creates a standardized report bundle (JSON and Log) for Audiotown.
    """
    if not report_path or not report_path.is_dir():
        logger.stream(
            f" Cannot find {report_path} or the report path is invalid.",
            err=True,
            fg="yellow",
        )
        return False

    report_path.mkdir(parents=True, exist_ok=True)
    metadata = [
        "Software Name: Audiotown",
        f"Version: f{audiotown.__version__}",
        f"timestamp: {datetime.now().isoformat()}",
        f"User: {Path.home().name}",
        f"Python: {platform.python_version()}",
        f"OS: {platform.platform()}",
        f"folder: {str(stats_folder.absolute())}",
        f"report_folder: {str(report_path.resolve())}",
    ]
    # meta_text = "\n".join(metadata)
    # metadata = dataclasses.asdict(MetaContent())
    meta_text = MetaContent().to_text()
    meta_text = meta_text + "\n" + "\n".join(
        [
            f"stats_folder: {str(stats_folder.absolute())}",
            f"report_folder: {str(report_path.resolve())}",
        ]
    )
    # Pathlib writes (Clean & Fast)
    Path(report_path / "meta.txt").write_text(meta_text, encoding="utf-8")

    Path(report_path / "run.log").write_text(
        logger.get_full_log(), encoding="utf-8"
    )

    json_data = {"metadata": metadata, "data": dataclasses.asdict(stats)}
    json_file = report_path / "stats.json"
    try:
        json_data = json.dumps(
            json_data, indent=4, ensure_ascii=False, cls=AudiotownEncoder
        )
        json_file.write_text(json_data, encoding="utf-8")

        logger.stream(f"'report' dir: {report_path.resolve()}")
    except Exception as e:
        logger.stream(
            f"[!] Failed to export report: {e}. Error Type: {type(e).__name__}",
            err=True,
        )
        return False

    return True
