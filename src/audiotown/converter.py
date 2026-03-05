import subprocess
import json
from pathlib import Path
from audiotown.logger import SessionLogger
from audiotown.logger import logger
from audiotown.consts import AudioFormat, FFmpegConfig,bitrate_map
from audiotown.utils import find_external_cover
from audiotown.stats import get_stream_info, probe_file
from typing import Tuple


def convert_flac_to_apple_friendly(
        file_path: Path,
        target: AudioFormat,
        target_path: Path,
        ff_config:FFmpegConfig,
        logger: SessionLogger,
        bit_rate:str = bitrate_map["medium"],
        dry_run: bool = False,
        # verbose: bool = False
        ) -> Tuple[bool, str]:
    """
    Converts a single FLAC to ALAC (m4a) with cover art integration. Support both lossless (alac) and lossy (aac)
    Returns True if successful, False otherwise.
    """
    if not target_path:
        output_path = target_folder.with_suffix(target.ext) # Apple-friendly format .m4a
    else:
        output_path = target_path

    ffmpeg_path, ffprobe_path = ff_config.ffmpeg_path, ff_config.ffprobe_path

    # 1. INSPECT: Does it have embedded artwork?
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
        "-loglevel", "error",
        "-y",
        "-i", str(file_path),
    ]
    # Add cover input only if it exists
    # Only add cover.jpg as an input if no embedded art is found
    art_copy_method = "copy"
    if external_artwork_path and has_external_artwork:
        cmd.extend(["-i", str(external_artwork_path)])
        if 'png' in external_artwork_path.suffix.lower():
             art_copy_method = "mjpeg"
    
    # Stream mapping 
    cmd.extend(["-map", "0:a:0"]) # Map audio from 1st input
    if has_embedded_artwork:
        cmd.extend(["-map", "0:v:0"]) # Map embedded art from source (1st input)
    elif has_external_artwork:
        cmd.extend(["-map", "1:v:0"]) # Map external art from 2nd input
    
    # encoding
    cmd.extend(["-c:a", target.encoder]) # 'alac' or 'aac'
    
    if target.encoder == "aac":
        # for aac encoder. default to medium quality
        default_quality = "medium"
        selected_bitrate = bit_rate if bit_rate in list(bitrate_map.values()) else bitrate_map.get(default_quality)  or "256k"
        cmd.extend(["-b:a", selected_bitrate])
    cmd.extend([
        "-c:v", str(art_copy_method),
        "-disposition:v:0", "attached_pic",
        "-map_metadata", "0",
        "-y", str(output_path)
    ])

    if dry_run: 
        probe_cmd = [
            ffprobe_path, 
            "-v", "error",
            "-show_entries", 
            "stream=sample_rate,bits_per_raw_sample,bits_per_raw_sample,bit_rate, channels:format=duration:format_tags=title,artist,album,date,genre,",
            "-of", "json", 
            str(file_path)
        ]

        try:
            res = subprocess.run(probe_cmd, capture_output=True, text=True)
            data = json.loads(res.stdout)
            stream = data.get("streams", [{}])[0]
            format_data = data.get("format", {})
            tags = format_data.get("tags", {})
            if tags and len(tags):
                tags={str(k).lower().strip(): v for k,v in tags.items()}
            # 2. Robust Extraction
            s_rate = f"{int(stream.get('sample_rate', 0)) // 1000}kHz" if stream.get('sample_rate') else "??kHz"
            
            # We use .get() with None, then handle it
            raw_bits = stream.get("bits_per_raw_sample","") or stream.get("bits_per_sample","")
            b_depth = f"{raw_bits}bit" if raw_bits and raw_bits != "0" else "??bit"
            
            channels = f"{stream.get('channels', '?')}ch"
            
            # 3. Concise vs. Detailed Info
            quality_str = f"{s_rate}/{b_depth}/{channels}"
            
        except Exception:
            quality_str = "Metadata Error"
            tags = {}
        # Standard Concise Output
        # logger.log(f"[DRY-RUN] {file_path.name} ({quality_str}) \t -> \t {output_path.name}")
        
        # Optional: Additional Info only if verbose is triggered
        if verbose:
            title = tags.get("title", "Unknown")
            artist = tags.get("artist", "Unknown")
            album = tags.get("album", "Unknown")
            # logger.log(f"Tags: {artist} - {title} - {album}")
        
        return True, ""

    try:

        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, # Capture stderr (2>)
            text=True
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            # logger.stream(f"  FFMPEG ERROR on {file_path.name}: {stderr}", fg="red")
            # click.secho(f"  FAILED: {file_path.name}\n  Error: {stderr}", fg="red")
            return False, f"Unexpected error: {stderr}"
        
        # logger.stream(f"SUCCESS: {file_path.name}", fg="green")
        return True, ""
    except subprocess.CalledProcessError as e:
        # logger.stream(f"CRITICAL: {str(e)}", fg="red")
        return False, f"CRITICAL: {str(e)}"