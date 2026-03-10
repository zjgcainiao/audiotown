import subprocess
import json
import os
from typing import Tuple
from pathlib import Path
from audiotown.logger import SessionLogger
from audiotown.logger import logger
from audiotown.consts import AudioFormat,  BitrateTier, AppContext, AppConfig, ConversionTask, ConversionTaskResult, ConversionDetail, ConversionReport
from audiotown.utils import find_external_cover
from audiotown.stats import probe_file
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

def convert_flac_to_apple_friendly(
    file_path: Path,
    target: AudioFormat,
    target_path: Path,
    app_context: AppContext,
    bit_rate: str = "",
) -> Tuple[bool, str]:
    """
    Converts a single FLAC to ALAC (m4a) with cover art integration. Support both lossless (alac) and lossy (aac)
    Returns True if successful, False otherwise.
    """
    # Apple-friendly format .m4a
    if not target_path:
        output_path = target_folder.with_suffix(
            target.ext
        )  
    else:
        output_path = target_path

    ffmpeg_path = app_context.ff_config.ffmpeg_path if app_context.ff_config else None
    ffprobe_path = app_context.ff_config.ffprobe_path if app_context.ff_config else None
    if not ffmpeg_path or not ffprobe_path:
        return False, "error. missing dependencies"

    # 1. INSPECT: Does it have embedded artwork
    audio_record = probe_file(file_path, ffprobe_path)
    if not audio_record:
        return False, ""
    has_embedded_artwork = audio_record.has_embedded_artwork
    # 2. CHECK: Is there a local cover.jpg?
    has_external_artwork = False
    external_artwork_path = None
    if not has_embedded_artwork:
        external_artwork_path = find_external_cover(file_path.parent)
        has_external_artwork = external_artwork_path is not None
    cmd = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i", str(file_path),
    ]
    # Add cover input only if it exists
    # Only add cover.jpg as an input if no embedded art is found
    art_copy_method = "copy"
    if external_artwork_path and has_external_artwork:
        cmd.extend(["-i", str(external_artwork_path)])
        if "png" in external_artwork_path.suffix.lower():
            art_copy_method = "mjpeg"

    # Stream mapping
    cmd.extend(["-map", "0:a:0"])  # Map audio from 1st input
    if has_embedded_artwork:
        cmd.extend(["-map", "0:v:0"])  # Map embedded art from source (1st input)
    elif has_external_artwork:
        cmd.extend(["-map", "1:v:0"])  # Map external art from 2nd input

    # encoding
    cmd.extend(["-c:a", target.encoder])  # 'alac' or 'aac'

    if target.encoder == AudioFormat.AAC.codec_name:
        # for aac encoder. default to medium quality
        # default_quality = "medium"
        selected_bitrate = (
            bit_rate
            if bit_rate in app_context.app_config.supported_bitrates
            else BitrateTier.MEDIUM.value
        )
        cmd.extend(["-b:a", selected_bitrate])
    cmd.extend(
        [
            "-c:v",
            str(art_copy_method),
            "-disposition:v:0",
            "attached_pic",
            "-map_metadata",
            "0",
            "-y",
            str(output_path),
        ]
    )

    if app_context.dry_run:
        probe_cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "stream=sample_rate,bits_per_raw_sample,bits_per_raw_sample,bit_rate, channels:format=duration:format_tags=title,artist,album,date,genre,tracks",
            "-of",
            "json",
            "-i",
            str(file_path),
        ]

        try:
            res = subprocess.run(probe_cmd, capture_output=True, text=True)
            data = json.loads(res.stdout)
            stream = data.get("streams", [{}])[0]
            format_data = data.get("format", {})
            tags = format_data.get("tags", {})
            if tags and len(tags):
                tags = {str(k).lower().strip(): v for k, v in tags.items()}
            # 2. Robust Extraction
            s_rate = (
                f"{int(stream.get('sample_rate', 0)) // 1000}kHz"
                if stream.get("sample_rate")
                else "??kHz"
            )

            # We use .get() with None, then handle it
            raw_bits = stream.get("bits_per_raw_sample", "") or stream.get(
                "bits_per_sample", ""
            )
            b_depth = f"{raw_bits}bit" if raw_bits and raw_bits != "0" else "??bit"

            channels = f"{stream.get('channels', '?')}ch"

            # 3. Concise vs. Detailed Info
            quality_str = f"{s_rate}/{b_depth}/{channels}"

        except Exception:
            quality_str = "Metadata Error"
            tags = {}
            return False, ""
        return True, ""

    # temp output before the conversion completes
    temp_output = str(output_path) + ".tmp"


    # 2. Add the '-threads 1' flag to your 'cmd' list
    # This prevents 8 FFmpegs from fighting over the same CPU cores
    cmd.insert(1, "-threads")
    cmd.insert(2, "1")

    try:

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Capture stderr (2>)
            text=True,
            errors='replace'
        )
        # stdout, stderr_data = process.communicate()
        # We wait for the process to finish
        process.wait()
        stderr_data = ""
        if process.returncode != 0:
            stderr_data = process.stderr.read() if process.stderr else ""
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return False, f"FFmpeg Error (Code {process.returncode}): {stderr_data.strip()}"

        # SUCCESS: Log the stderr because that contains the bitrate/codec info
        if stderr_data:
            os.rename(temp_output, output_path)
            return True, f"FFmpeg Output: {stderr_data.strip()}"
    except subprocess.CalledProcessError as e:
        # logger.stream(f"CRITICAL: {str(e)}", fg="red")
        return False, f"CRITICAL: {str(e)}"
    except FileNotFoundError:
        return False, "CRITICAL: ffmpeg binary not found. Check your AppConfig/PATH."
    except Exception as e:
        return False, f"CRITICAL: System error: {str(e)}"

    return True, ""


# -------------------
# multiple theading helper functions
# -------------------

def convert_task_wrapper(task_data: ConversionTask) -> ConversionTaskResult:
    """
    Unpacks the dict and returns (file_path, success, message)
    """
    file_path = task_data.file_path
    success, msg = convert_flac_to_apple_friendly(
        file_path,
        task_data.target,
        task_data.output_path,
        task_data.app_context,
        task_data.bitrate,
    )
    return ConversionTaskResult(file_path, success, msg)



import click
def run_parallel_conversion(all_tasks: List[ConversionTask]) -> List[ConversionTaskResult]:
    """
    The main engine driver. 
    Input: A list of ConversionTask dictionaries.
    Output: A list of results (path, success, message).
    """
    results: List[ConversionTaskResult] = []
    max_workers = max(1, (os.cpu_count() or 4) - 1)
    # this following is a setup for I/O bound while converison is cpu intensive. 
    # max_workers = AppConfig().MAX_WORKERS
    # conv_report = ConversionReport()
    with click.progressbar(length=len(all_tasks),
                        label=click.style("In progress", fg="cyan", bold=True),
                        fill_char=click.style("█", fg="cyan"),
                        show_pos=True,  # This is the magic! Shows '12/2030'
                        show_percent=True,  # Shows '45%'
                        empty_char=click.style("░", fg="white", dim=True),  # The 'Solid' look
                        color=True,
                        ) as bar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks at once
            future_to_path = {executor.submit(convert_task_wrapper, t): t.file_path for t in all_tasks}

            for future in as_completed(future_to_path):
                task_result = future.result()
                results.append(task_result)
                bar.update(1) # This makes the bar move smoothly for every file
                
    return results