import os
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional, Iterable, Generator
from audiotown.logger import logger
from audiotown.utils import sanitize_metadata
from audiotown.consts import (
    AudioRecord,
    AudioFormat,
    AppConfig,
    FolderStats,
    AudioStream,
)

def get_stream_info(
    file_path: Path, ffprobe_path: str, stream_level: int = 2
) -> Optional[AudioStream]:
    """Uses 'ffprobe' to inspect the file and find video/audio streams.
    file_path: a single audio file. Path object.

    level 1: selective entries are shown
    level 2: full scope of streams and format
    """
    if not file_path.is_file():
        logger.stream(f"{file_path} does not exist or can't be opened", fg="red")
        return None
    cmd_1 = [
        ffprobe_path,
        "-hide_banner",
        "-v",
        "quiet",
        "-show_entries",
        "stream=sample_rate,bits_per_raw_sample,bits_per_raw_sample,bit_rate, channels:format=duration:format_tags=title,artist,album,date,genre,track,",
        "-of",
        "json",
        "-i",
        str(file_path),
    ]
    cmd_2 = [
        ffprobe_path,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        "-i",
        str(file_path),
    ]
    if stream_level == 1:
        cmd = cmd_1
    elif stream_level == 2:
        cmd = cmd_2
    else:
        cmd = cmd_1

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result:
        raw_json = json.loads(result.stdout)
        data = AudioStream.from_ffprobe_json(raw_json)
        return data
    else:
        return None


def probe_file(file_path: Path, ffprobe_path: str) -> Optional[AudioRecord]:
    """
    Takes an file path input and does `ffprobe` probing.
    Returns a AudioRecord instance or None
    """
    if not file_path.is_file():
        logger.stream(f"Invalid file: {file_path}", fg="red")
        return None
    suffix = file_path.suffix.casefold()
    if not suffix or not AudioFormat.is_supported(suffix):
        logger.stream(f"Suffix not supported or not available.", fg="yellow")
        return None
    try:
        data = get_stream_info(file_path, ffprobe_path)
        is_readable = True

        if not data:
            is_readable = False
            raise Exception
        format_data = data.format
        stream = data.streams[0] if data.streams and len(data.streams) > 0 else {}
        if not data.streams or not stream:
            logger.stream(
                f"can't detect any audio streams in the file. file may not be corrupted. check again.",
                err=True,
            )
            is_readable = False
            raise Exception
        if format_data.get("tags"):
            format_tags = {
                k.lower().strip(): v for k, v in format_data.get("tags", {}).items()
            }
        else:
            format_tags = {}

        # -- internal helper function
        def _cleanse_fields(
            data: dict, keys: list = ["artist", "album", "title", "genre", "year","track_name"]
        ):
            result = []
            for key in keys:
                string = data.get(key, "").casefold()
                if not len(string) or not (string.strip()):
                    string = "unknown"

                string = sanitize_metadata(string)
                result.append(string)
            return result

        # 2. extract sample_rate, bits,codec_name, etc
        sample_rate = int(stream.get("sample_rate", 0))
        raw_bits = int(
            stream.get("bits_per_raw_sample", 0)
            or stream.get("bits_per_sample", 0)
        )
        channels = int(stream.get("channels", 0))

        s_rate = (
            f"{int(stream.get('sample_rate', 0)) // 1000}kHz"
            if stream.get("sample_rate")
            else "??kHz"
        )
        b_depth = f"{raw_bits} bit" if raw_bits and raw_bits != "0" else "?? bit"

        quality_str = f"{s_rate}/{b_depth}/{channels} bits"

        codec_type = stream.get("codec_type", "")  # audio or video
        codec_name = stream.get("codec_name", "")  # actual codec
        duration = float(
            stream.get("duration", 0.00) or format_data.get("duration", 0.00) 
        )
        bitrate_bps = stream.get("bit_rate", 0) or format_data.get("bit_rate", 0) 
        artist_name, album_name, title_name, genre_name, year_name,track_name = _cleanse_fields(
            format_tags, ["artist", "album", "title", "genre", "date", "track_name"]
        )

        fingerprint = str(artist_name.casefold() + "_" + title_name.casefold())

        audio_format = AudioFormat.from_codec(codec_name)
        if not audio_format:
            return None

        has_embedded_artwork = any(s.get("codec_type") == "video" for s in data.streams)
        size_bytes = int(format_data.get("size", 0) or file_path.stat().st_size or 0)

        record = AudioRecord(
            file_path=file_path,
            audio_format=audio_format,
            bitrate_bps=bitrate_bps or 0,
            sample_rate_hz=sample_rate,
            bits_per_sample=raw_bits,
            channels=channels,
            size_bytes=size_bytes,
            duration_sec=duration,
            year=year_name,
            artist=artist_name,
            album=album_name,
            title=title_name,
            genre=genre_name,
            readable=is_readable,
            fingerprint=fingerprint,
            error="",
            has_embedded_artwork=has_embedded_artwork,
            track=track_name,
        )

        return record
    except Exception as e:
        try:
            audio_format = AudioFormat.from_suffix(file_path.suffix.casefold())
            if not audio_format:
                return None
        except Exception as e:
            return None
        unreadable_rec = AudioRecord(
            file_path=file_path,
            audio_format=audio_format,
            bitrate_bps=0,
            sample_rate_hz=0,
            bits_per_sample=0,
            duration_sec=0,
            size_bytes=file_path.stat().st_size,  # get it via `file.stat()`
            channels=0,
            year="0",
            album="",
            artist="",
            genre="",
            title="",
            readable=False,
            fingerprint=str(" " + "_" + " "),
            error=str(e),
            track= " ",
        )
        return unreadable_rec

def get_audio_files(
    directory: Path, formats: Optional[Iterable[AudioFormat]] = None
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

    if formats:
        target_suffixes = {fmt.ext for fmt in formats}
    else:

        target_suffixes = AudioFormat.supported_extensions()

    # .rglob is recursive (finds files in subfolders)
    for file in directory.rglob("*"):  # Grab every file
        # Check if the file's suffix (lowercased) is in our allowed set
        # if AudioFormat.is_supported(file.suffix):
        if file.suffix.lower() in target_suffixes:
            yield file

def get_folder_stats(
    folder: Path,
    ffprobe_path: str,
    max_workers: int = AppConfig().MAX_WORKERS,
)-> FolderStats:
    """Gathers technical and metadata stats for a folder."""

    stats = FolderStats(folder_path=folder)
    # Define our 'Music & Audiobook' whitelist

    all_files = list(get_audio_files(folder))
    # SUPPORTED = AppConfig().supported_extensions
    # supported_str = ", ".join(SUPPORTED)
    # logger.stream(
    #     f"Scanning files ending in one of the ({supported_str}) in {folder.resolve().stem}..."
    # )
    logger.stream(f"{len(all_files):,} Found...", fg="cyan")


    import click
    with click.progressbar(
            length=len(all_files),
            label=click.style("Processing files",fg='cyan',bold=True),
            show_percent=True,   # Shows '45%'
            show_pos=True, # Shows [120/13000]
            fill_char=click.style('█',fg='cyan',bold=True),
            empty_char=click.style("░", fg="white", dim=True),
        ) as bar:
            
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 2. Submit all tasks
            futures = {executor.submit(probe_file, f, ffprobe_path): f for f in all_files}
            
            # 3. Process as they finish
            for future in as_completed(futures):
                record = future.result()
                
                if record:
                    stats.add(record)
                
                # 4. Update the bar immediately
                bar.update(1)
                
    return stats