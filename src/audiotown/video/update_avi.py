from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import subprocess
from typing import Any


# ---------- data models ----------
@dataclass(slots=True)
class ProbeInfo:
    path: str
    duration: str | None
    video_codec: str | None
    audio_codec: str | None
    width: int | None
    height: int | None
    fps: str | None


# @dataclass(slots=True)
# class RemuxResult:
#     source: str
#     output: str
#     status: str                  # success | retry_success | failed | skipped
#     attempt: str                 # copy | genpts | none
#     returncode: int | None
#     message: str
#     probe: ProbeInfo | None

@dataclass(slots=True)
class RemuxResult:
    source: str
    output: str
    status: str
    attempt: str
    returncode: int | None
    message: str


# ---------- terminal helpers ----------

def print_header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_section(title: str) -> None:
    print()
    print(f"[{title}]")


def print_ok(msg: str) -> None:
    print(f"  OK     {msg}")


def print_warn(msg: str) -> None:
    print(f"  WARN   {msg}")


def print_fail(msg: str) -> None:
    print(f"  FAIL   {msg}")


def print_info(msg: str) -> None:
    print(f"  INFO   {msg}")


# ---------- subprocess helpers ----------

def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# ---------- ffprobe ----------

def probe_file(path: Path) -> ProbeInfo | None:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries",
        "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json",
        str(path),
    ]
    result = run_cmd(cmd)

    if result.returncode != 0:
        return None

    try:
        data: dict[str, Any] = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    streams = data.get("streams", [])
    fmt = data.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    return ProbeInfo(
        path=str(path),
        duration=fmt.get("duration"),
        video_codec=video_stream.get("codec_name"),
        audio_codec=audio_stream.get("codec_name"),
        width=video_stream.get("width"),
        height=video_stream.get("height"),
        fps=video_stream.get("r_frame_rate"),
    )



def format_fps(fps: str | None) -> str:
    if not fps:
        return "?"
    if "/" in fps:
        num, den = fps.split("/", 1)
        try:
            return f"{float(num) / float(den):.3f}"
        except (ValueError, ZeroDivisionError):
            return fps
    return fps

# ------------------
def validate_output(src: Path, dst: Path) -> tuple[bool, str]:
    if not dst.exists():
        return False, "output file missing"

    size_bytes = dst.stat().st_size
    if size_bytes < 100 * 1024:
        return False, f"output too small: {size_bytes} bytes"

    src_probe = probe_file(src)
    dst_probe = probe_file(dst)

    if dst_probe is None:
        return False, "ffprobe failed on output"

    if not dst_probe.duration:
        return False, "output duration missing"

    try:
        src_dur = float(src_probe.duration) if src_probe and src_probe.duration else 0.0
        dst_dur = float(dst_probe.duration) if dst_probe.duration else 0.0
    except ValueError:
        return False, "duration parse failed"

    if src_dur > 0 and abs(src_dur - dst_dur) > 3:
        return False, f"duration mismatch: src={src_dur:.3f}s dst={dst_dur:.3f}s"

    return True, "ok"


# ------------------
def cleanup_bad_output(dst: Path) -> None:
    if dst.exists():
        try:
            dst.unlink()
        except OSError:
            pass
# ---------- ffmpeg remux ----------

import shlex

def try_remux(src: Path, dst: Path) -> RemuxResult:
    print_info(f"src={src}")
    print_info(f"dst={dst}")

    cmd_copy = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "warning",
        "-y",
        
        "-fflags", "+genpts",
        "-i", str(src),
        "-map", "0",
        "-c", "copy",
        "-movflags", "+faststart",
        str(dst),
    ]
    # for avi to mp4. Maintain quality
    cmd_copy_mp4 = [
        "ffmpeg", "-hide_banner", 
        "-loglevel", "warning",
          "-y",
        "-fflags", "+genpts",
        "-i", str(src),
        "-map", "0",
        "-c", "copy",
        # -c:s mov_text \
        #  -map 0:v -map 0:a? -map 1:0 \
        # -c:v copy -c:a copy -c:s mov_text \
        "-movflags", "+faststart",
        str(dst),
    ]

    # avi to mp4. maximize comptaiblity
    cmd_transcode_mp4 = [
    "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
    "-fflags", "+genpts",
    "-i", str(src),

    "-map", "0:v:0",
    "-map", "0:a?",
    "-map", "0:s?",

    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "medium",
    "-crf", "22",

    "-c:a", "aac",
    "-b:a", "192k",

    "-c:s", "mov_text",
    "-movflags", "+faststart",

    str(dst),
]
    # manual override for testing

    cmd_copy = cmd_transcode_mp4

    print_info(f"cmd={shlex.join(cmd_copy)}")
    result_copy = run_cmd(cmd_copy)

    print_info(f"returncode={result_copy.returncode}")

    if result_copy.stderr.strip():
        print_info("ffmpeg stderr tail:")
        for line in result_copy.stderr.strip().splitlines()[-12:]:
            print_info(line)

    print_info(f"dst.exists()={dst.exists()}")
    if dst.exists():
        print_info(f"dst.size={dst.stat().st_size/1024**2:.1f} Mbytes")

    if result_copy.returncode != 0:
        return RemuxResult(
            source=str(src),
            output=str(dst),
            status="failed",
            attempt="copy",
            returncode=result_copy.returncode,
            message=result_copy.stderr.strip() or "ffmpeg failed",
        )

    if not dst.exists():
        return RemuxResult(
            source=str(src),
            output=str(dst),
            status="failed",
            attempt="copy",
            returncode=0,
            message="ffmpeg returned success but output file is missing",
        )

    if dst.stat().st_size < 500 * 1024:
        return RemuxResult(
            source=str(src),
            output=str(dst),
            status="failed",
            attempt="copy",
            returncode=0,
            message=f"ffmpeg returned success but output is suspiciously small: {dst.stat().st_size} bytes",
        )

    return RemuxResult(
        source=str(src),
        output=str(dst),
        status="success",
        attempt="copy",
        returncode=0,
        message="remux succeeded",
    )
# ---------- main workflow ----------

def find_avi_files(root: Path) -> list[Path]:
    # return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".mkv")
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".avi")


def main() -> None:
    
    root = Path(".").resolve()
    if len(find_avi_files(root)) == 0:
        print_info('no path in the current work dir, try the default folder `/Volumes/Media`.')
        root = Path("/Volumes/Media").expanduser().resolve()

    # print_header("AVI -> MKV REMUX PROTOTYPE")
    print_header("AVI -> MP4 REMUX PROTOTYPE")
    print_info(f"Root: {root}")

    avi_files = find_avi_files(root)
    if not avi_files:
        print_warn("No AVI files found.")
        return

    print_info(f"Found {len(avi_files)} AVI file(s).")

    results: list[RemuxResult] = []

    for idx, avi_path in enumerate(avi_files, start=1):
        # out_path = avi_path.with_suffix(".mkv")
        out_path = avi_path.with_suffix(".mp4")

        print_section(f"{idx}/{len(avi_files)}  {avi_path}")

        probe = probe_file(avi_path)
        if probe is None:
            print_warn("ffprobe failed or returned unreadable JSON.")
        else:
            print_info(
                f"video={probe.video_codec} "
                f"audio={probe.audio_codec} "
                f"size={probe.width}x{probe.height} "
                f"fps={probe.fps} "
                f"duration={probe.duration}"
            )

        result = try_remux(avi_path, out_path)
        results.append(result)

        if result.status == "success":
            print_ok(f"{result.message}")
            print_info(f"output={result.output}")
        elif result.status == "retry_success":
            print_warn("Initial remux failed; retry path used.")
            print_ok(f"{result.message}")
            print_info(f"output={result.output}")
        elif result.status == "skipped":
            print_warn(result.message)
            print_info(f"output={result.output}")
        else:
            print_fail(f"attempt={result.attempt} returncode={result.returncode}")
            print_fail(result.message.splitlines()[-1] if result.message else "Unknown error")

    # summary
    success_count = sum(r.status == "success" for r in results)
    retry_success_count = sum(r.status == "retry_success" for r in results)
    skipped_count = sum(r.status == "skipped" for r in results)
    failed_count = sum(r.status == "failed" for r in results)

    print_header("SUMMARY")
    print_info(f"Success        : {success_count}")
    print_info(f"Retry success  : {retry_success_count}")
    print_info(f"Skipped        : {skipped_count}")
    print_info(f"Failed         : {failed_count}")

    # optional: write report
    report_path = root / "avi_remux_report.json"
    report_data = [asdict(r) for r in results]
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    print_info(f"Report written : {report_path}")


if __name__ == "__main__":
    main()