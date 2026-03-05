import json
import platform
import datetime
from pathlib import Path
from audiotown.logger import SessionLogger, logger
from audiotown.consts import FolderStats, AudiotownEncoder

def div_blocks( number: int, divider:str = "= ") -> str:
    """Generates a repeating block of characters."""
    count = number if number > 0 else 5
    return (divider * count).strip()

def div_section_line(message: str = "", level: int = 1) -> str:
    """Creates a centered section line with consistent padding."""
    match level:
        case 1:
            blocks = div_blocks(10,"= ")
        case 2:
            blocks = div_blocks(5,"- ")
        case _:
            blocks = div_blocks(10,"= ")
    if not message:
        return blocks
    return f"{blocks} {message.strip()} {blocks}"


def format_section(title: str, data: dict) -> str:
    blocks = div_blocks(2,"*")
    title_line = f"{blocks} {title} {blocks}"
    if not data:
        return title_line + "\n(empty)"

    # stringify keys/values; you can also prettify keys here if you want
    items = [(str(k), data[k]) for k in data.keys()]
    width = max(len(k) for k, _ in items) + 2

    lines = [title_line]
    for k, v in items:
        lines.append(f" {k:<{width}}: {v}")
    lines.append(f"{blocks} End of {title} {blocks}")
    return "\n".join(lines)



def create_report_for_convert(report_dir: Path, results: dict, logger: SessionLogger):
    # 1. Ensure the directory exists
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Save JSON (The data)
    with open(report_dir / "report.json", "w") as f:
        json.dump(results, f, indent=4)
        
    # 3. Save Session Log (The "tee" output)
    with open(report_dir / "session.log", "w") as f:
        # Use the getter method we built in the SessionLogger class
        f.write(logger.get_full_log())
        
    # 4. Save Meta.txt (The context)
    meta_content = [
        "Software Name: Audiotown",
        f"Dry Run: {results['summary']['is_dry_run']}",
        # f"Run Time: {results['run_time']}",
        f"User: {Path.home().name}",
        "Python: {platform.python_version()}",
        f"OS: {platform.platform()}",
    ]
    # Inside the meta.txt logic
    # meta_content.append(f"Total Duration: {results['summary']['duration_seconds']}s")

    with open(report_dir / "meta.txt", "w") as f:
        f.write("\n".join(meta_content))

import json
import dataclasses
from datetime import datetime
from pathlib import Path

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

def generate_report_for_stats(base_path: Path, stats_folder: Path, stats: FolderStats):
    """
    Creates a standardized report bundle (JSON and Log) for Audiotown.
    """

    report_path = base_path/f"audiotown_stats"
    report_path.mkdir(parents=True, exist_ok=True)
    metadata = [
            # "version": "0.1.0",
            "Software Name: Audiotown",
            f"timestamp: {str(datetime.now().isoformat())}",
            f"User:: {Path.home().name}",
            f"Python: {platform.python_version()}",
            f"OS: {platform.platform()}",
            f"stats_folder: {str(stats_folder.absolute())}",
            f"report_folder: {str(report_path.resolve())}",
            "status: success",
        ]
    with open(report_path / "meta.txt", "w") as f:
        f.write("\n".join(metadata))


    with open(report_path / "session.log", "w") as f:
        # Use the getter method we built in the SessionLogger class
        f.write(logger.get_full_log())
        
    report_bundle = {
        "metadata": metadata,
        "data": dataclasses.asdict(stats)
    }
    json_filename = report_path / "stats.json"
    try:
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(report_bundle, f, indent=4, ensure_ascii=False,
                      cls=AudiotownEncoder)
            
        logger.stream(f"Report exported: {json_filename.parent.absolute()}")
    except Exception as e:
        logger.stream(
                f"[!] Failed to export report: {e}. Type: {type(e).__name__}",
                err=True
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

    # Note: Your logger is already handling the run.log file elsewhere
    # but you could easily add a call here to move/copy it if needed.
