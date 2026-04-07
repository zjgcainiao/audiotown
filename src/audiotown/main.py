import time
import click
import shutil
import sys
import subprocess
from pathlib import Path
from wcwidth import wcswidth
from typing import Optional, NoReturn, Tuple, Union, List
from audiotown.utils import (
    format_section,
    div_blocks,
    div_section_line,
    safe_division,
    to_int,
    size_string,
    duration_string,
)

from audiotown.consts.app_context import AppContext
from audiotown.consts import (
    AudioFormat,
    FFmpegConfig,
    BitrateTier,
    AppConfig,
    TypeSummary,
    DuplicateGroup,
    CmdArgsConfig,
    ConversionDetail,
    ConversionReport,
    ConversionTask,
    ConversionTaskResult,
)
from audiotown.logger import logger, SessionLogger
from audiotown.report import create_report_for_convert, generate_report_for_stats
from audiotown.services.scan_service import ScanService
from audiotown.services.convert_service import ConvertService

app_config = AppConfig()
app_context = AppContext(
    start_time=time.perf_counter(), 
    app_config=app_config, 
    ff_config=FFmpegConfig.create(),
    logger=logger
)


# --- Boostrap Helpers ---
def abort(message: str, code: int = 1) -> NoReturn:
    """Prints an error message and exits the application."""
    logger.stream(f"\nx {message}", fg="red", err=True)
    sys.exit(code)


def ensure_ffmpeg() -> Tuple[str, str]:
    """Checks for ffmpeg  & ffprobe and offers to install them via 'Homebrew' if missing.
    handles CLI startup/install flow. """
    ffmpeg_path: Optional[str]
    ffprobe_path: Optional[str]

    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if ffmpeg_path and ffprobe_path:
        return ffmpeg_path, ffprobe_path
    logger.stream("Required dependency 'ffmpeg' or 'ffprobe' is missing.", fg="yellow")

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


# --- main cli --
@click.group(chain=False, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=str(app_config.version), prog_name="audiotown")
@click.pass_context
def cli_runner(ctx: click.Context):
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
    # ctx.ensure_object(dict)
    # # ctx.ensure_object(AppContext)
    # ctx.obj["start_time"] = time.perf_counter()
    # divs_lvl1 = app_config.divs_lvl1

    # logger.stream(f"{divs_lvl1} Audiotown CLI Starting {divs_lvl1}", bold=True)
    # ffpmeg_path, ffprobe_path = ensure_ffmpeg()
    # ff_config: FFmpegConfig = FFmpegConfig(ffpmeg_path, ffprobe_path)
    # if not ff_config:
    #     abort("Missing Dependencies. Exited unexpected.")
    # app_context.ff_config = ff_config

    # # ctx.obj["app_config"]= app_config
    # ctx.obj = app_context
    app_ctx = AppContext.ensure_app_ctx(ctx)
    app_ctx.start_time = time.perf_counter()

    divs_lvl1 = app_ctx.app_config.divs_lvl1
    
    logger.stream(f"{divs_lvl1} Audiotown CLI Starting {divs_lvl1}", bold=True)
    ffmpeg_path, ffprobe_path = ensure_ffmpeg()

    app_ctx.ff_config = FFmpegConfig(ffmpeg_path, ffprobe_path)
    # ctx.obj = app_ctx

@cli_runner.result_callback()
@click.pass_context
def process_result(ctx: click.Context, result, **kwargs):
    # 2. TEARDOWN: This runs AFTER the subcommand finishes
    app_context = AppContext.get_app_ctx(ctx)
    start_time = app_context.start_time
    divs_lvl1 = app_context.app_config.divs_lvl1
    # logger.stream(f'Debug. In result_callback(), app_context.dry_run: {app_context.dry_run}\n')
    if start_time:
        run_time = time.perf_counter() - start_time
        app_context.run_time = run_time
        logger.stream(f"Run time: {run_time:.1f} s\n")
    if app_context.report_path is None:
        logger.stream("Use '--report-path' flag to export a full set of logs.")

    logger.stream(f"Type 'audiotown' for help.")
    section_line = div_section_line("End of Audiotown CLI", 1)
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
        AudioFormat.codec_choices(), case_sensitive=False
    ),
    default=AudioFormat.ALAC.codec_name,
    help="audio encoder (Default is ALAC, Apple Lossless Format)",
)
@click.option(
    "--bitrate",
    type=click.Choice(BitrateTier.supported_bitrates(), case_sensitive=False),
    default=None,
    # show_default=True,
    help="Target bitrate for AAC. (Ignored for ALAC)",
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
@click.option(
    "--video",
    "video_container",

              )
def convert_cmd(
    ctx: click.Context,
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
    # app_context = AppContext.get_app_ctx(ctx)
    app_context = AppContext.get_app_ctx(ctx)
    app_context.report_path = report_path
    app_context.dry_run = dry_run
    logger = app_context.logger
    if not app_context or not app_context.app_config or not app_context.ff_config:
        abort("Unexpected error. missing dependencices")

    logger.stream(f"{div_section_line('Converting',2)}")
    divs_lvl2 = app_context.app_config.divs_lvl2
    search_formats = [
        AudioFormat.FLAC,
    ]
    search_codecs = [item.codec_name for item in search_formats]
    search_exts = [item.ext for item in search_formats]
    if not app_context and not app_context.ff_config.ffmpeg_path:
        logger.stream(
            "Error: ffmpeg/ffprobe not detected on system path.", fg="red", err=True
        )
        abort("Error: ffmpeg/ffprobe not detected on system path")


    if app_context.dry_run:
        logger.stream(">>> Dry Run (Preview) mode: ON", fg="cyan")
    
    folder = folder.resolve()
    output_base = Path(folder / f"audiotown_export")

    target = AudioFormat.from_codec(codec) if codec else AudioFormat.ALAC
    if target is None:
        raise click.BadParameter(f"Unsupported codec: {codec}")
    
    # Detect if the user EXPLICITLY provided a bitrate
    user_provided_bitrate = bitrate is not None

    # 2. Assign the actual working bitrate (Fallback to MEDIUM if None)
    effective_bitrate = bitrate if user_provided_bitrate else BitrateTier.MEDIUM.value
    s_bitrate = ""
    if not target:
        abort("Command exited unexpected. unknown format(s).")

    if not target.is_lossless:
        # We don't need to check 'if bitrate in supported' because
        # click.Choice already validated this for us!
        s_bitrate = f"(bitrate_kbps: {effective_bitrate})"

    logger.stream(
        f"  {f"source format":<16} : {" ".join(search_codecs):<{len(search_codecs)}} "
    )
    logger.stream(f"  {f"output format":<16} : {codec:<{len(codec)+1}} {s_bitrate}")
    # ONLY show warning if it's lossless AND the user specifically typed --bitrate
    if target.is_lossless and user_provided_bitrate:
        logger.stream("Ignore bitrate for loss less conversion.", fg="yellow")
    default_folder = str(Path(".").resolve())
    if not folder:
        # logger.stream(message="Missing a directory. you MUST enter one.",fg="red", err=True)
        abort("Missing a directory. you MUST enter one.")

    # 1. Find files
    scan_service = app_context.get_scan_service()
    files = list(scan_service.get_audio_files(folder, search_formats))
    total = len(files)
    if not total:
        logger.stream("No file found.", fg="yellow")
        return
    else:
        logger.stream(f"{total} Found...", fg="cyan")

    # conv_report = ConversionReport()

    # internal_helper
    def _computer_output_path(file_path: Path) -> Path:
        file_path = file_path.resolve()
        relative_path = file_path.relative_to(folder)
        target_path = Path(output_base / relative_path).with_suffix(target.ext)
        return target_path

    conv_tasks: List[ConversionTask] = []
    
    # 1. Identify all unique folders needed
    required_dirs = { _computer_output_path(f).parent for f in files }

    # 2. Create them once
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)

    # 3. Now the loop only focuses on building Tasks
    conv_tasks = [
        ConversionTask(
            file_path=f,
            target=target,
            output_path=_computer_output_path(f),
            # app_context=app_context,
            bitrate=bitrate, 
        )
        for f in files
    ]
   
    convert_service = app_context.get_convert_service()
    # logger.stream(f'app_context.dry_run: {app_context.dry_run}\n')
    # logger.stream(f'convert_service dry_run stats: {convert_service.dry_run}\n')
    with click.progressbar(
        length=len(conv_tasks),
        label=click.style("In progress", fg="cyan", bold=True),
        fill_char=click.style("█", fg="cyan"),
        show_pos=True,
        show_percent=True,
        empty_char=click.style("░", fg="white", dim=True),
        color=True,
    ) as bar:
        conv_task_results = convert_service.run_parallel_conversion(
            conv_tasks,
            progress_callback=lambda done, total: bar.update(1),
        )
    # conv_task_results = run_parallel_conversion(conv_tasks)
    conv_details = [
        ConversionDetail(
            str(result.file_path),
            str(_computer_output_path(result.file_path)),
            "Success" if result.success else "Failed",
            result.message,
        )
        for result in conv_task_results
    ]
    success_count = sum(1 for r in conv_task_results if r.success)
    total_count = len(conv_task_results)
    failed_count = total_count - success_count
    conv_report = ConversionReport(
        folder_path = folder,
        total=total_count,
        success=success_count,
        failed = failed_count,
        details=conv_details
    )
    logger.stream(f"{div_section_line('Completed',2)}\n")

    # Add to results for the JSON
    logger.stream(
        format_section(
            "Summary",
            {"total": total_count, "success": success_count, "failed": failed_count},
        )
    )
    logger.stream(" ")
    logger.stream(f" export dir: {str(output_base)}")

    if app_context.report_path is not None:
        base_dir = app_context.report_path.resolve()
        final_dir = Path(base_dir / app_context.app_config.EXPORT_DIR_NAME)

        # create the report dir
        final_dir.mkdir(parents=True, exist_ok=True)
        # rp_success = create_report_for_convert(final_dir, results, logger=app_context.logger)
        rp_success, err_msg = create_report_for_convert(
            final_dir, conv_report, logger=app_context.logger
        )
        logger.stream(
            f" report dir: {str(Path(final_dir).resolve())}",
        )


# ----------------
# SUBCOMMAND 2: stats
# ----------------
@cli_runner.command(name="stats")
@click.pass_context
@click.option(
    "--report-path",
    is_flag=False,
    flag_value=".",
    type=click.Path(path_type=Path),
    help="Generate logs/JSON. Defaults to current directory if no path given.",
)
@click.option(
    "--find-duplicate",
    is_flag=True,
    flag_value=True,
    type=bool,
    help=" to enable duplicate file searching, etc.",
)
@click.argument("folder", type=click.Path(exists=True, path_type=Path))
def stats_cmd(
    ctx: click.Context,
    folder: Path,
    report_path: Path,
    find_duplicate: bool = False,
):
    """Stats Dashboard & Insight tool."""
    if not folder or not folder.is_dir():
        abort(f"Error. Cannot open the folder {folder} or it does not exists.")
    # start_perf = time.perf_counter() # More accurate for measuring duration
    app_context = AppContext.get_app_ctx(ctx)
    # if not app_context.ff_config:
    #     abort(f"Exited unexpected. system depenendecies missing.")
    tops = app_context.app_config.TOPS or 5
    lvl2_blocks = app_context.app_config.divs_lvl2  # div_blocks(5, "- ")

    # Helper for sorting: Sort by count (desc) then name (asc)
    def sort_logic(item: Tuple[str, Union[TypeSummary, DuplicateGroup]]):
        return (-item[1].count, item[0].lower())

    def sort_logic_for_dupls(item: Tuple[str, Union[TypeSummary, DuplicateGroup]]):
        return (-(item[1].count > 1), item[0].lower())

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

    # SUPPORTED = AppConfig().supported_extensions
    SUPPORTED = app_context.app_config.supported_extensions
    supported_str = ", ".join(SUPPORTED)
    logger.stream(
        f"Scanning audio files ending in one of the ({supported_str}) in {folder.resolve().stem}..."
    )
    probe_service = app_context.get_probe_service()
    # probe_service = ProbeService(app_context.ff_config.require_ffprobe())
    scan_service = ScanService(probe_service=probe_service)
    all_files = list(scan_service.get_audio_files(folder))
    
    # logger.stream(f"scan_service: {scan_service}", fg="red")
    logger.stream(f"{len(all_files):,} Found...", fg="cyan")


    # helper function for click.progressbar
    last_reported = 0
    def _on_progress(done: int, total: int) -> None:
        nonlocal last_reported
        if done % 5 == 0 or done == total:
            delta = done - last_reported
            bar.update(delta)
            last_reported = done
            
    with click.progressbar(
        length=len(all_files),
        label=click.style("Processing files", fg="cyan", bold=True),
        show_percent=True,  # Shows '45%'
        show_pos=True,  # Shows [120/13000]
        fill_char=click.style("█", fg="cyan", bold=True),
        empty_char=click.style("░", fg="white", dim=True),
    ) as bar:
        stats = scan_service.get_folder_stats(
                files=all_files,
                # ffprobe_path=app_context.ff_config.ffprobe_path,
                folder_path=folder,
                # progress_callback=lambda done, total: bar.update(1),
                progress_callback=_on_progress,
            )

    logger.stream(f"{div_section_line("Stats", 2)}\n")
    # logger.stream(f'app_context.ff_config: {app_context.ff_config}\n')
    # logger.stream(f'all_files[1]: {all_files[1]}\n')
    # logger.stream(f'stats: {stats}')
    total_size_bytes = 0
    total_gb = stats.total_bytes / app_config.GIGA_BYTES
    # hour_format = (
    #     f"{stats.total_duration_sec/app_config.SECS_PER_DAY:,.1f} days"
    #     if stats.total_duration_sec / app_config.SECS_PER_HOUR > 200
    #     else f"{stats.total_duration_sec/ app_config.SECS_PER_HOUR:,.1f} hours"
    # )
    hour_format = duration_string(stats.total_duration_sec)
    logger.stream(
        f"Your library can play {hour_format} in one row, contains {stats.total_files:,} files, and takes up {total_gb:.1f} GB.",
    )

    sorted_artists = sorted(stats.artists.items(), key=sort_logic)
    top_artists = sorted_artists[:tops]
    if top_artists and top_artists[0]:
        top_one_artist, top_one_data = top_artists[0]
        logger.stream(
            f"You collect work from {len(stats.artists):,} distinct artists. The top one in your list is {str(top_one_artist)} ({top_one_data.count} songs)."
        )

    sorted_genres = sorted(stats.genres.items(), key=sort_logic)
    top_genres = sorted_genres[:tops]
    if top_genres:
        top_one_genre, top_genre_data = top_genres[0]

        logger.stream(
            f"Based on the library, you favor this genre the most: {str(top_one_genre)} ({top_genre_data.count:,} songs).\n"
        )

    sorted_families = sorted(
        stats.by_family.items(),
        key=sort_logic,  # x[0] is the key, x[1] is the TypeSummary object
    )
    for family_name, data in sorted_families:
        total_size_bytes += int(data.size_bytes)
        size_mb = data.size_bytes / app_context.app_config.MEGA_BYTES
        size_str = f"{size_mb/1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
        family_str = f"{safe_division(100*data.count, stats.total_files):>4.0f} % is {family_name.title()}"
        logger.stream(family_str)
    logger.stream(" ")
    readable_str = f"{safe_division(100 * stats.readable_files, stats.total_files ):>4.0f} % is readable"
    logger.stream(f"{readable_str}")

    unreadable_str = f"{safe_division(100* (stats.total_files-stats.readable_files), stats.total_files ):>4.0f} % is unreadable"
    logger.stream(f"{unreadable_str}\n")

    # embedded artwork
    if stats.by_has_embedded_artwork:
        cnt_embedded_artwork = stats.by_has_embedded_artwork[
            "has_embedded_artwork"
        ].count
        embedded_artwork_pc = f"{safe_division(100 * cnt_embedded_artwork, stats.total_files ):>4.0f} % contains embedded thumbnail or artwork."
        logger.stream(f"{embedded_artwork_pc}\n", bold=True)
    if stats.bloated_files and len(stats.by_bloated):
        saved_size_mb = (
            0.3
            * stats.by_bloated["bloated"].size_bytes
            / app_context.app_config.MEGA_BYTES
        )
        saved_size_str = (
            f"{saved_size_mb/1024:.1f} GB"
            if saved_size_mb > 1024
            else f"{saved_size_mb:.1f} MB"
        )

        bloated_str = f"We've found {int(stats.bloated_files)} files (potential .wav, .pcm files) that can be converted to flac without damaging your hearing experience. It may save {saved_size_str}."
        logger.stream(bloated_str)
    else:
        # f"\nnumber of file considered bloated: {float(stats.bloated_files)}"
        bloated_str = ""

    # logger.stream("\n")
    if safe_division(100 * stats.readable_files, stats.total_files) or 0 > 0.95:
        comment_str = "Your media library looks healthy. Majority of your records are readable and in good conditions."
        logger.stream(f"{comment_str}\n", bold=True, fg="green")
    else:
        comment_str = ""

    # --- 1. Top Extensions (by file count) ---
    logger.stream(
        f"Top {min(tops,len(stats.by_ext))} Extensions (by file count):", fg="cyan"
    )
    sorted_exts = sorted(stats.by_ext.items(), key=sort_logic)
    top_exts = sorted_exts[:tops]
    sub_total_name = "Total # of Extensions"
    label_width = (
        max(
            max((display_width(ext) for ext, _ in top_exts), default=0),
            len(sub_total_name),
        )
        + 1
    )
    for ext, data in top_exts:

        total_size_bytes += int(data.size_bytes)
        size_mb = data.size_bytes / 1024**2
        size_str = f"{size_mb/1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
        logger.stream(
            f"  {ljust_display(ext,label_width)} : {data.count:>7,} files ({size_str:>8})"
        )

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
            + 1
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
            + 1
        )
        for album, data in top_albums:
            count = data.count
            logger.stream(f"  {ljust_display(album, label_width)}: {count:>7,}")
        logger.stream(
            f"  {ljust_display('Total # of Albums', label_width)}: {len(stats.albums):>7,}\n",
            dim=True,
        )

    # --- 4. Top Genres (Still sorted by count, then A-Z) ---
    if stats.genres:
        logger.stream(
            f"Top {min(app_config.TOPS,len(stats.genres))} Genres (by file count):",
            fg="cyan",
        )

        sub_total_name = "Total # of Genres"
        label_width = (
            max(
                max((display_width(genre) for genre, _ in top_genres), default=0),
                len(sub_total_name),
            )
            + 1
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
        sorted_quality_tiers = sorted(stats.by_tier.items(), key=sort_logic)
        sub_total_name = "Total # of Quality Tiers"
        label_width = (
            max(
                max(
                    (
                        display_width(quality_tier)
                        for quality_tier, _ in sorted_quality_tiers[:tops]
                    ),
                    default=0,
                ),
                len(sub_total_name),
            )
            + 1
        )

        for quality_tier, data in sorted_quality_tiers:
            total_size_bytes += int(data.size_bytes)
            size_mb = data.size_bytes / app_config.MEGA_BYTES
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

    if find_duplicate and len(stats.fingerprints):

        sub_total_name = "total # of dupl. groups"
        waste_size_string = "potential waste size to save"
        duplicate_items = [
            (key, val) for key, val in stats.fingerprints.items() if val.count > 1
        ]
        sorted_fps = sorted(duplicate_items, key=sort_logic)
        label_width = (
            # max(
            max(
                (
                    display_width(duplicate_key)
                    for duplicate_key, _ in sorted_fps[: min(tops, len(sorted_fps))]
                ),
                default=0,
            )
            # len(sub_total_name),
            # len(waste_size_string),
            # )
        )
        fn_str_width = 40
        # logger.stream(f'{min(app_config.TOPS,len(sorted_fps))}')
        total_waste_bytes = 0

        if sorted_fps:

            for _, data in sorted_fps:
                total_waste_bytes += data.waste_size
            sorted_fps = sorted_fps[: min(app_config.TOPS, len(sorted_fps))]
            logger.stream(
                f"Top {min(app_config.TOPS,len(sorted_fps))} Possible Duplicate Groups (by file count):",
                fg="cyan",
            )
            for dp_key, data in sorted_fps:
                recs = data.records
                if len(recs) > 1:
                    sorted_recs = sorted(
                        data.records,
                        key=lambda x: (
                            not x.audio_format.is_lossless,
                            -(to_int(x.bitrate_bps)),
                            dp_key,
                        ),
                    )
                else:
                    sorted_recs = recs
                selected = min(app_config.TOPS, len(sorted_recs))
                sorted_recs = sorted_recs[:selected]
                size_mb = data.size_bytes / app_config.MEGA_BYTES
                size_str = (
                    f"{size_mb/1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
                )
                fname_str = ""
                if sorted_recs:
                    strs = [
                        ("'" + rec.file_path.name + "'" or "")
                        for rec in sorted_recs
                        if rec
                    ]
                    fname_str = ", ".join(strs)

                if not fname_str:
                    fname_str = fname_str
                logger.stream(
                    f"  {ljust_display(dp_key.title(),label_width)} : {data.count:>6,} ({size_str:>8}) "
                )
                logger.stream(
                    f"      |-->  {ljust_display(fname_str,fn_str_width) + ', etc.'}",
                    dim=True,
                )

            logger.stream(
                f"  {ljust_display(sub_total_name, label_width)} : {len(sorted_fps):>6,}\n",
                dim=True,
            )
            logger.stream(
                f"  {ljust_display('total size to save ', label_width)} : {(total_waste_bytes/1024**3):>6,.1f}\n",
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
        logger.stream(f"  FFmpeg detected:  {ffmpeg_p}", fg="green")
        logger.stream(f"  FFprobe detected: {ffprobe_p}", fg="green")
        logger.stream("Ready!", bold=True)

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
