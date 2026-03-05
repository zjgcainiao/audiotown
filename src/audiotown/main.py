import click
import shutil
import sys
import subprocess
import datetime
import time
from pathlib import Path
from wcwidth import wcswidth
from typing import Optional, NoReturn, Tuple
from audiotown.converter import convert_flac_to_apple_friendly
from audiotown.stats import get_folder_stats, get_audio_files
from audiotown.consts import AudioFormat, FFmpegConfig,bitrate_map
from audiotown.logger import logger
from audiotown.report import (
    create_report_for_convert,
    format_section,
    div_blocks,
    div_section_line,
    generate_report_for_stats,
)


# --- Boostrap Helpers ---
def abort(message: str, code: int = 1) -> NoReturn:
    """Prints an error message and exits the application."""
    logger.stream(f"\nx {message}", fg="red", err=True)
    sys.exit(code)


def ensure_ffmpeg() -> Tuple[str, str]:
    """Checks for ffmpeg and offers to install it via 'Homebrew' if missing."""
    ffmpeg_path: Optional[str] = shutil.which("ffmpeg")
    ffprobe_path: Optional[str] = shutil.which("ffprobe")

    if ffmpeg_path and ffprobe_path:
        return ffmpeg_path, ffprobe_path
    logger.stream("Required dependency 'ffmpeg' or 'ffprobe' is missing.", err=True)

    # Check if Homebrew itself is installed first
    if not shutil.which("brew"):
        abort(
            "'ffmpeg' is missing and Homebrew is not installed. Please install Homebrew first: https://brew.sh"
        )

    if click.confirm(
        "Would you like me to try installing ffmpeg via Homebrew for you?"
    ):
        logger.stream("Running 'brew install ffmpeg'... this may take a minute.")
        try:
            # We use 'check=True' so it raises an error if the install fails
            subprocess.run(["brew", "install", "ffmpeg"], check=True)
            new_ffmpeg_path = shutil.which("ffmpeg")
            new_ffprobe_path = shutil.which("ffprobe")
            if new_ffmpeg_path and new_ffprobe_path:
                logger.stream("'ffmpeg' installed successfully!", fg="green")
                return new_ffmpeg_path, new_ffprobe_path
        except subprocess.CalledProcessError:
            abort(
                "Homebrew failed to install 'ffmpeg'. Please try running 'brew install ffmpeg' manually."
            )
    abort("audiotown cannot run without ffmpeg.")


@click.group(chain=False, context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
def cli_runner(ctx):
    """
    AudioTown: A toolkit for Apple-optimized music libraries. It offers
    lossless to apple alac/aac conversion and detailed overview for any selected media folders.
    The idea is to lets see what we can do with what we got.

    Quick Start:

    1. Run `audiotown check` to verify your FFmpeg setup.

    2. Run `audiotown stats .` to see your library overview.

    3. Run `audiotown convert .` to start your conversion.
    """
    # 1. SETUP: This runs BEFORE any subcommand
    ctx.ensure_object(dict)
    ctx.obj["start_time"] = time.perf_counter()
    divs_lvl1 = div_blocks(10, "= ")
    ctx.obj["divs_lvl1"] = divs_lvl1
    ctx.obj["divs_lvl2"] = div_blocks(5, "- ")
    logger.stream(f"{divs_lvl1} Audiotown CLI Starting {divs_lvl1}", bold=True)
    ffpmeg_path, ffprobe_path = ensure_ffmpeg()
    ff_config: FFmpegConfig = FFmpegConfig(
        ffmpeg_path=ffpmeg_path, ffprobe_path=ffprobe_path
    )
    ctx.obj["ff_config"] = ff_config


@cli_runner.result_callback()
@click.pass_context
def process_result(ctx, result, **kwargs):
    # 2. TEARDOWN: This runs AFTER the subcommand finishes
    start_time = ctx.obj.get("start_time")
    divs_lvl1 = ctx.obj.get("divs_lvl1") or div_blocks(10, "= ")
    if start_time:
        duration = time.perf_counter() - start_time
        logger.stream(f"Run time: {duration:.1f} s\n")

        logger.stream(f"Use '--report-path' flag to export a full set of logs.")
        logger.stream(f"Type 'audiotown' for help.")
        section_line = div_section_line("Ended", 1)
        logger.stream(f"{section_line}", bold=True)


# ----------------
# SUBCOMMAND 1: convert
# ----------------
@cli_runner.command(name="convert")
@click.pass_context
@click.argument("folder", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--codec",
    type=click.Choice(
        [AudioFormat.ALAC.codec_name, AudioFormat.AAC.codec_name], case_sensitive=False
    ),
    default=AudioFormat.ALAC.codec_name,
    help="audio encoder (Default is ALAC, Apple Lossless Format)",
)
@click.option(
    "--bitrate",
    default="256k",
    help="Bitrate for AAC (e.g., 128k, 256k, 320k). Ignored for ALAC.",
)
@click.option("--dry-run", is_flag=True, help="Preview the result. Default: False")
# @click.option("--verbose", is_flag=True, help="Verbose output")
@click.option(
    "--report-path",
    "report_path",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=Path),
    flag_value=".", 
    default=None,
    help="A folder where a set of detailed logs will be generated. If no path provided, defaults to the source folder.",
)
def convert_cmd(
    ctx,
    folder: Path,
    codec: str,
    report_path: Optional[Path],
    dry_run: bool,
    bitrate: str,
) -> None:
    """Convert FLACs in FOLDER to Apple-friendly formats.
    # Logic:
    # 1. codec is 'alac' -> ignore bitrate.
    # 2. codec is 'aac' -> apply bitrate to ffmpeg command.
    """
    # validation resources: ffmpeg
    ff_config = ctx.obj.get("ff_config")
    divs_lvl2 = ctx.obj.get("divs_lvl2")
    search_formats = [
        AudioFormat.FLAC,
    ]
    search_codecs = [item.codec_name for item in search_formats]
    search_exts = [item.ext for item in search_formats]
    if not ff_config:
        logger.stream(
            "Error: ffmpeg/ffprobe not detected on system path.", fg="red", err=True
        )
        abort("Error: ffmpeg/ffprobe not detected on system path")

    # if not dry_run:
    #     click.confirm(f"This will search and convert files in folder {folder.resolve().name}. Continue?", abort=True)

    logger.stream(f"{div_section_line('Converting',2)}")
    if dry_run:
        logger.stream(">>> Dry Run (Preview) mode: ON", fg="cyan")

    folder = folder.resolve()
    output_base = folder / f"audiotown_export"
    if codec:
        target = AudioFormat.from_codec(codec)
    else:
        target = AudioFormat.ALAC
    target = AudioFormat.from_codec(codec) if codec else AudioFormat.ALAC
    s_bitrate = ""
    if not target:
        abort("Command exited unexpected. unknown format(s).")
    if target.is_lossless and bitrate:
        logger.stream(f"Ignore bitrate for lossless conversion(s).", fg="yellow")
    if not target.is_lossless and bitrate:
        if not bitrate in list(bitrate_map.values()):
            bitrate=bitrate_map["medium"]
            logger.stream(f"! Uncceptable bitrate. default to {bitrate}",fg="yellow")
        s_bitrate = f"(bitrate_bkps: {str(bitrate)})"
    logger.stream(f" source format(s): {search_codecs} ")

    logger.stream(f" destin format: {codec} {s_bitrate}")

    default_folder = str(Path(".").resolve())
    if not folder:
        # logger.stream(message="Missing a directory. you MUST enter one.",fg="red", err=True)
        abort("Missing a directory. you MUST enter one.")

    # 1. Find files

    files = list(get_audio_files(folder, search_formats))
    ext_string = ", ".join(search_exts)
    total = len(files)
    if total == 0:
        logger.stream("No file found.", fg="yellow")
        return

    logger.stream(f"{total} Found. Starting conversion...", fg="cyan")

    results = {
        "start_time": str(
            datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        ),
        "summary": {"total": 0, "success": 0, "failed": 0},
        "details": [],
    }

    with click.progressbar(
        files,
        label="Converting",
    ) as bar:
        for file_path in bar:
            # bar.label = f"Processing {file_path.name[:25]}..."
            bar.update(0)  # Refresh the bar display without moving the percentage
            file_path = file_path.resolve()
            relative_path = file_path.relative_to(folder)
            target_path = Path(output_base / relative_path).with_suffix(target.ext)
            target_path.parent.mkdir(parents=True, exist_ok=True)  # Create subfolders!
            success, error_message = convert_flac_to_apple_friendly(
                file_path, target, target_path, ff_config, logger, bitrate, dry_run, 
            )

            # Record the result
            results["summary"]["total"] += 1
            if success:
                logger.log(
                    f"\n Success: {file_path.name[:25]} --> {target_path.name[:25]} "
                )
                results["summary"]["success"] += 1
            else:
                results["summary"]["failed"] += 1

            # Add this to make the report.json useful!
            results["details"].append(
                {
                    "source": str(file_path),
                    "destination": str(
                        target_path
                    ),  # Pass target_path into your result list
                    "status": "SUCCESS" if success else "FAILED",
                }
            )
    # section_line = div_section_line('Conversion Completed',2)
    logger.stream(f"{div_section_line('Conversion Completed',2)}")

    # Add to results for the JSON
    # results["summary"]["duration_seconds"] = round(duration, 2)
    results["summary"]["is_dry_run"] = str(dry_run)
    logger.stream(format_section("Summary", results["summary"]))
    logger.stream(" ")
    logger.stream(f"output dir: {str(output_base)}")

    if report_path:
        base_dir = report_path.resolve()
        # 1. Create a timestamped folder name
        timestamp = datetime.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        bundle_dir = base_dir / f"audiotown_convert"

        logger.stream(
            f"report dir: {str(Path(bundle_dir).resolve())}",
        )
        # 2. Create and populate
        bundle_dir.mkdir(parents=True, exist_ok=True)
        create_report_for_convert(bundle_dir, results, logger)


# ----------------
# SUBCOMMAND 2: stats
# ----------------
@cli_runner.command(name="stats")
@click.pass_context
@click.option('--report-path', is_flag=False, flag_value=".", 
              type=click.Path(path_type=Path),
              help="Generate logs/JSON. Defaults to current directory if no path given.")
@click.argument("folder", type=click.Path(exists=True, path_type=Path))
def stats_cmd(
    ctx,
    folder: Path,
    report_path:Path,
):
    """Stats Dashboard & Insight tool."""
    # start_perf = time.perf_counter() # More accurate for measuring duration
    ff_config = ctx.obj.get("ff_config", "")
    if not ff_config:
        abort(f"Exited unexpected. system depenendecies missing.")
    tops = 5
    lvl2_blocks = div_blocks(5, "- ")

    # Helper for sorting: Sort by count (desc) then name (asc)
    def sort_logic(item):
        return (-item[1].count, item[0].lower())

    def display_width(s: str) -> int:
        # wcswidth returns -1 for some unprintables; treat as 0-width fallback
        w = wcswidth(s)
        return w if w >= 0 else len(s)

    def ljust_display(s: str, width: int) -> str:
        pad = width - display_width(s)
        if pad <= 0:
            return s
        return s + (" " * pad)

    # logger.stream(f"{lvl2_blocks}Scan Library: {folder.name}{lvl2_blocks}", bold=True)
    stats = get_folder_stats(folder, ff_config.ffprobe_path)
    
    # --- 1. File Type Summary (Table-like) ---
    logger.stream(f"{div_section_line("Stats", 2)}\n")
    total_size_bytes = 0
    total_gb = stats.total_bytes / (1024**3)
    hour_format = f"{stats.total_duration_sec/3600/24:,.1f} days" if stats.total_duration_sec/3600 > 200 else f"{stats.total_duration_sec/3600:,.1f} hours"
    logger.stream(
        f"Your library can play {hour_format} in one row, contains {stats.total_files:,} files, and takes up {total_gb:.1f} GB."
    )

    sorted_artists = sorted(stats.artists.items(), key=sort_logic)
    top_artists = sorted_artists[:tops]
    top_one_artist, top_one_data = top_artists[0]
    logger.stream(f"You collect work from {len(stats.artists)-1:,} distinct artists. The top one in your list is {str(top_one_artist)} ({top_one_data.count} songs).")
    
    sorted_genres = sorted(stats.genres.items(), key=sort_logic)
    top_genres = sorted_genres[:tops]
    top_one_genre, top_genre_data = top_genres[0]

    logger.stream(f"Based on the library, you favors this genre the most: {str(top_one_genre)} ({top_genre_data.count:,} songs).\n")
    s_strs = []
    sorted_families = sorted(
        stats.by_family.items(),
        key=sort_logic,  # x[0] is the key, x[1] is the TypeSummary object
    )
    for family_name, data in sorted_families:
        total_size_bytes += int(data.size_bytes)
        size_mb = data.size_bytes / 1024**2
        size_str = f"{size_mb/1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
        family_str = (
            f"{float(data.count)/stats.total_files*100:>4.0f} % is {family_name.title()}"
        )
        logger.stream(family_str)
    logger.stream(" ")
    readable_str = (
        f"{float(stats.readable_files)/stats.total_files * 100:>4.0f} % is readable"
    )
    logger.stream(f"{readable_str}")
    
    unreadable_str = (
        f"{float(stats.total_files-stats.readable_files)/stats.total_files * 100:>4.0f} % is unreadable or encounters errors during probes"
    )   
    logger.stream(f"{unreadable_str}\n")
    if stats.bloated_files and len(stats.by_beloated):
        saved_size_mb = 0.3 * stats.by_beloated["beloated"].size_bytes / 1024**2
        saved_size_str = (
            f"{saved_size_mb/1024:.1f} GB"
            if saved_size_mb > 1024
            else f"{saved_size_mb:.1f} MB"
        )
        
        bloated_str = f"We've found {int(stats.bloated_files)} files (potential .wav, .pcm files) that can be converted to flac without damaging your hearing experience. It may save {saved_size_str}."
        logger.stream(bloated_str)
    else:
        # f"\nnumber of file considered beloated: {float(stats.bloated_files)}"
        bloated_str = "" 
    # logger.stream("\n")
    if float(stats.readable_files)/stats.total_files * 100 > 0.95:
        comment_str = "Your media library looks healthy. Majority of your records are readable and in good conditions."
        logger.stream(f"{comment_str}\n",bold=True,fg="green")
    else:
        comment_str = ""

    # --- 1. Top Extensions (by file count) ---
    
    logger.stream(f"Top {min(tops,len(stats.by_ext))} Extensions (by file count):", fg="cyan")

    sorted_exts = sorted(stats.by_ext.items(), key=sort_logic)
    top_exts = sorted_exts[:tops]
    sub_total_name = "Total # of Extensions"
    label_width = (
            max(
                max((display_width(ext) for ext, _ in top_exts ), default=0),
                len(sub_total_name),
            )
            + 2
    )
    for ext, data in top_exts:

        total_size_bytes += int(data.size_bytes)
        size_mb = data.size_bytes / 1024**2
        size_str = f"{size_mb/1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
        logger.stream(f"  {ljust_display(ext,label_width)} : {data.count:>7,} files ({size_str:>8})")

    # Total for File Distribution
    total_gb = stats.total_bytes / (1024**3)
    logger.stream(
        f"  {ljust_display(sub_total_name, label_width)} : {len(stats.by_ext):>7,} \n",
        dim=True,
    )

    # --- 2. Artists (by file count) ---
    if stats.artists:
        logger.stream(
            f"Top {min(tops,len(stats.artists))} Artists (by file count):",
            fg="cyan",
            bold=True,
        )

        max_artist_len = (
            max(
                max((display_width(artist) for artist, _ in top_artists), default=9),
                len("Total # of Artists"),
            )
            + 2
        )
        for artist, data in sorted_artists[:tops]:
            count = data.count
            logger.stream(f"  {ljust_display(artist, max_artist_len)}: {count}")
        logger.stream(
            f"  {ljust_display('Total # of Artists', max_artist_len)}: {len(stats.artists):,}\n",
            dim=True,
        )

    # --- 3. Albums (Sorted A-Z) ---
    if stats.albums:
        logger.stream(
            f"Top {min (tops,len(stats.albums))} Albums (by file count):",
            fg="cyan",
            bold=True,
        )
        sorted_albums = sorted(stats.albums.items(), key=sort_logic)
        top_albums = sorted_albums[:tops]
        label_width = (
            max(
                max((display_width(album) for album, _ in top_albums), default=0),
                len("Total # of Albums"),
            )
            + 2
        )
        # print(f"max ablum length: {label_width}")
        for album, data in top_albums:
            count=data.count
            logger.stream(f"  {ljust_display(album, label_width)}: {count:>7,}")
        logger.stream(
            f"  {ljust_display('Total # of Albums', label_width)}: {len(stats.albums):>7,}\n",
            dim=True,
        )

    # --- 4. Top Genres (Still sorted by count, then A-Z) ---

    if stats.genres:
        logger.stream(
            f"Top {min(tops,len(stats.genres))} Genres (by file count):", fg="cyan"
        )

        sub_total_name = 'Total # of Genres'
        label_width = (
            max(
                max((display_width(genre) for genre, _ in top_genres), default=0),
                len(sub_total_name)
                )+ 2
        )
        for genre, data in sorted_genres[:tops]:
            count = data.count
            logger.stream(f"  {genre:<{label_width}}: {count:>7,}")
        logger.stream(
            f"  {ljust_display(sub_total_name, label_width)}: {len(stats.genres):>7,}\n",
            dim=True,
        )
    if len(stats.by_tier):
        logger.stream(f"Fine Grained Quality Tier (by file count):", fg="cyan")
        sorted_quality_tiers = sorted(
            stats.by_tier.items(),
            key=sort_logic 
        )
        sub_total_name = "Total # of Quality Tiers"
        label_width = (
            max(
                max((display_width(quality_tier) for quality_tier, _ in sorted_quality_tiers[:tops]), default=0),
                len(sub_total_name),
            )
            + 2
        )
        
        for quality_tier, data in sorted_quality_tiers:
            total_size_bytes += int(data.size_bytes)
            size_mb = data.size_bytes / 1024**2
            size_str = (
                f"{size_mb/1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
            )

            logger.stream(
                f"  {ljust_display(quality_tier.title(),label_width)} : {data.count:>7,} ({size_str:>8})"
            )
        logger.stream(
            f"  {ljust_display(sub_total_name, label_width)} : {len(stats.by_tier):>7,}\n",
            dim=True,
        )

    if report_path:
        # If the user just typed '--report-path', this will be Path(".")
        # We ensure the directory exists
        report_path.mkdir(parents=True, exist_ok=True)
        generate_report_for_stats(report_path, folder, stats)
    logger.stream(f"{lvl2_blocks} End of Stats {lvl2_blocks} ")


# ----------------
# SUBCOMMAND 3: check
# ----------------
@cli_runner.command(name="check")
def check_cmd():
    """Verify that FFmpeg and dependencies are correctly installed."""
    logger.stream("Checking dependencies...")
    try:
        # Re-use your existing bootstrap helper
        ffmpeg_p, ffprobe_p = ensure_ffmpeg()

        # If we reach here, they exist
        logger.stream(f"  FFmpeg found:  {ffmpeg_p}", fg="green")
        logger.stream(f"  FFprobe found: {ffprobe_p}", fg="green")
        logger.stream("Ready to go!", bold=True)

    except click.Abort:
        # ensure_ffmpeg already printed the error, so we just exit
        abort("Command exited unexpectedly.")


# ----------------
# SUBCOMMAND 4: inspect
# ----------------
# @cli_runner.command(name="inspect")
# @click.argument('folder', type=click.Path(exists=True, path_type=Path))
# @click.option('--find-duplicate', is_flag=True)
# def inspect_cmd(folder: Path,find_duplicate:bool = False):
#     # --- 4. Operational Flags ---
#     if find_duplicate:
#         logger.stream(f"{div_blocks(2,"-")} Duplicate Check: {div_blocks(2,"-")}", fg="yellow", bold=True)
#         for (artist, title), paths in stats["fingerprints"].items():
#             if len(paths) > 1:
#                 logger.stream(f"  Found {len(paths)} copies of '{title}' by '{artist}':")
#                 for p in paths:
#                     # Show the size/bitrate so you know which one to delete!
#                     logger.stream(f"    - {str(p)} ")

#         logger.stream(f"{div_blocks(2,"-")} End of Duplicate Check {div_blocks(2,"-")}", fg="yellow", bold=True)


if __name__ == "__main__":
    cli_runner()
