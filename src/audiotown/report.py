import json
import platform
import dataclasses
from datetime import datetime
from pathlib import Path
from audiotown.logger import SessionLogger, logger
from audiotown.consts import FolderStats, AudiotownEncoder
import audiotown

def create_report_for_convert(
    report_dir: Path, results: dict, logger: SessionLogger
) -> bool:
    try:
        # 1. Ensure the directory exists
        if not report_dir or not report_dir.is_dir():
            logger.stream(
                f" Cannot find {report_dir} or the report path is invalid.",
                err=True,
                fg="yellow",
            )
            return False

        # 2. Save JSON
        json_data = json.dumps(
            results,
            indent=4,
            ensure_ascii=False,
        )
        Path(report_dir / "report.json").write_text(json_data, encoding="utf-8")

        # 3. Save Session Log (The "tee" output)
        Path(report_dir / "session.log").write_text(
            logger.get_full_log(), encoding="utf-8"
        )

        # 4. Save Meta.txt (The context)
        meta_content = [
            f"Software Name: Audiotown",
            f"Dry Run: {results['summary']['is_dry_run']}",
            # f"Run Time: {results['run_time']}",
            f"User: {Path.home().name}",
            "Python: {platform.python_version()}",
            f"OS: {platform.platform()}",
        ]
        # Write into meta.txt
        Path(report_dir / "meta.txt").write_text(
            "\n".join(meta_content), encoding="utf-8"
        )
        meta_text = "\n".join(meta_content)

        # Pathlib writes (Clean & Fast)
        Path(report_dir / "meta.txt").write_text(meta_text, encoding="utf-8")

        return True
    except Exception as e:
        logger.stream(
            f"Error: unexpected error occurred when exporting the report. {e}",
            err=True,
            fg="yellow",
        )
        return False


def find_tuple_keys(obj, path="root"):
    hits = []

    def walk(x, p):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(k, tuple):
                    hits.append(f"{p} -> tuple key {repr(k)}")
                walk(v, f"{p}[{repr(k)}]")
        elif isinstance(x, (list, tuple)):
            for i, item in enumerate(x):
                walk(item, f"{p}[{i}]")

    walk(obj, path)
    return hits


def generate_report_for_stats(
    base_path: Path, stats_folder: Path, stats: FolderStats
) -> bool:
    """
    Creates a standardized report bundle (JSON and Log) for Audiotown.
    """
    if not base_path or not base_path.is_dir():
        logger.stream(
            f" Cannot find {base_path} or the report path is invalid.",
            err=True,
            fg="yellow",
        )
        return False

    report_path = base_path / f"audiotown_stats"
    report_path.mkdir(parents=True, exist_ok=True)
    metadata = [
        # "version": "0.1.0",
        "Software Name: Audiotown",
        f"Version: f{audiotown.__version__}"
        f"timestamp: {datetime.now().isoformat()}",
        f"User: {Path.home().name}",
        f"Python: {platform.python_version()}",
        f"OS: {platform.platform()}",
        f"stats_folder: {str(stats_folder.absolute())}",
        f"report_folder: {str(report_path.resolve())}",
        "status: success",
    ]
    meta_text = "\n".join(metadata)

    # Pathlib writes (Clean & Fast)
    Path(report_path / "meta.txt").write_text(meta_text, encoding="utf-8")

    Path(report_path / "session.log").write_text(
        logger.get_full_log(), encoding="utf-8"
    )

    json_data = {"metadata": metadata, "data": dataclasses.asdict(stats)}
    json_file = report_path / "stats.json"
    try:
        json_data = json.dumps(
            json_data, indent=4, ensure_ascii=False, cls=AudiotownEncoder
        )
        json_file.write_text(json_data, encoding="utf-8")

        logger.stream(f"Report exported: {report_path.resolve()}")
    except Exception as e:
        logger.stream(
            f"[!] Failed to export report: {e}. Type: {type(e).__name__}", err=True
        )
        # tuple_hits = find_tuple_keys(report_bundle)
        # if tuple_hits:
        #     logger.stream("\n[!] Found tuple key(s):", err=True)
        #     for line in tuple_hits[:20]:
        #         logger.stream(f"\n    - {line}", err=True)
        #     if len(tuple_hits) > 20:
        #         logger.stream(f"\n    ... and {len(tuple_hits)-20} more", err=True)
        # else:
        #     logger.stream("\n[!] No tuple keys found. Error may be another non-JSON type.", err=True)

        return False

    return True
