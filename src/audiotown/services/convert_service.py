from __future__ import annotations
import json
import os
import subprocess
from typing import Callable
from pathlib import Path
# from audiotown.consts.ffmpeg_config import FFmpegConfig
# from audiotown.consts.app_context import AppContext
from audiotown.consts import video
from audiotown.consts.audio.audio_format import AudioFormat
from audiotown.consts.birate_tier import BitrateTier
from audiotown.consts.conversion import ConversionTask, ConversionTaskResult
from concurrent.futures import ThreadPoolExecutor, as_completed
from audiotown.services.command_builder_service import CommandBuilderService
from audiotown.video.policies.target_policy import AppleSafeMp4TargetPolicy
from audiotown.consts.video import video_record
from audiotown.consts.video.policy_decision import PolicyDecision
from audiotown.consts.video.video_container import VideoContainer
from audiotown.services.policy_service import PolicyService
from .probe_service import ProbeService
from audiotown.utils import find_external_cover
from audiotown.logger import SessionLogger
import logging
from audiotown.logger import logger

# logger = logging.getLogger(__name__)


class ConvertService:
    # def __init__(self, app_context:AppContext):
    #     self.app_context = app_context
    def __init__(
        self,
        ffmpeg_path: str,
        ffprobe_path: str,
        logger: SessionLogger,
        probe_service: ProbeService,
        supported_bitrates: set[str],
        dry_run: bool = False,
        verbose: bool = False,
    ) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.logger = logger
        self.supported_bitrates = supported_bitrates
        self.dry_run = dry_run
        self.verbose = verbose
        # self.probe_service = ProbeService(ffprobe_path=ffprobe_path)
        self.probe_service = probe_service

    # @classmethod
    # def from_appcontext(cls, app_context:AppContext) -> "ConvertService":
    #     if not app_context.ff_config.is_complete:
    #         raise RuntimeError("ffmpeg and ffprobe are required but not found in PATH")
    #     return cls(app_context=app_context)

    def convert_flac_to_apple_friendly(
        self,
        file_path: Path,
        target: AudioFormat,
        target_path: Path,
        bit_rate: str| None = None,
    ) -> tuple[bool, str]:
        """
        Converts a single FLAC to ALAC (m4a) with cover art integration. Support both lossless (alac) and lossy (aac)
        Returns True if successful, False otherwise.
        input args: 
            - file_path
            - target
            - target_path
            - bit_rate

        Returns:
            (success, message)
        """
        # Apple-friendly format .m4a
        if target_path is None:
            output_path = file_path.with_suffix(target.ext)
        else:
            output_path = target_path

        # 1. INSPECT: Does it have embedded artwork
        # probe_service = self.app_context.get_probe_service()
        # probe_service = ProbeService(ffprobe_path=FFmpegConfig().require_ffprobe())
        # audio_record = probe_file(file_path, ffprobe_path)

        try:
            audio_record = self.probe_service.probe_audio(file_path)
        except Exception as exc:
            return False, f"Failed to inspect file: {exc}"

        if audio_record is None:
            return False, "Unsupported or invalid file."
        if not audio_record.is_readable:
            err_msg = (audio_record.error or "").strip()
            if err_msg:
                return False, f"Error. File unreadable: {err_msg}"
            return False, "Error. File unreadable."

        has_embedded_artwork = audio_record.has_embedded_artwork
        # 2. CHECK: Is there a local cover.jpg?
        has_external_artwork = False
        external_artwork_path: Path | None = None
        if not has_embedded_artwork:
            external_artwork_path = audio_record.find_external_cover_art(
                file_path.parent
            )
            has_external_artwork = external_artwork_path is not None
        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(file_path),
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
                # if bit_rate in self.app_context.app_config.supported_bitrates
                if bit_rate in self.supported_bitrates
                else BitrateTier.MEDIUM.value
            )
            cmd.extend(["-b:a", selected_bitrate])
        # temp_output = str(output_path) + ".tmp"
        temp_output = output_path.with_name(
             f"{output_path.stem}.{os.getpid()}.tmp{output_path.suffix}"
        )
        temp_output_path = Path(temp_output)

        cmd.extend(
            [
                "-c:v",
                str(art_copy_method),
                "-disposition:v:0",
                "attached_pic",
                "-map_metadata",
                "0",
                "-y",
                str(temp_output),
            ]
        )
        # self.logger.log(f'this is the convert_flac inside the `ConvertService`....self.dry_run: {self.dry_run}')
        if self.dry_run:

            probe_cmd = [
                self.ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                # "stream=sample_rate,bits_per_raw_sample,bits_per_raw_sample,bit_rate, channels:format=duration:format_tags=title,artist,album,date,genre,tracks",
                "stream=sample_rate,bits_per_raw_sample,bit_rate,channels:"
                "format=duration:"
                "format_tags=title,artist,album,date,genre,track",
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

        # 2. Add the '-threads 1' flag to your 'cmd' list
        # This prevents 8 FFmpegs from fighting over the same CPU cores
        # cmd.insert(1, "-threads")
        # cmd.insert(2, "1")
        try:
            process = subprocess.Popen(
                cmd,
                # stdout=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,  # Capture stderr (2>)
                text=True,
                errors="replace",
            )
            # stdout, stderr_data = process.communicate()
            # We wait for the process to finish
            # process.wait()
            # stderr_data = None
            
            stdout_data, stderr_data = process.communicate()
            stderr_data = stderr_data or ""
            
            if process.returncode != 0:
                # stderr_data = process.stderr.read() if process.stderr else ""
                self._cleanup_bad_output(dst=temp_output_path)
                return (
                    False,
                    f"FFmpeg Error (Code {process.returncode}): {stderr_data.strip()}",
                )
            if not temp_output_path.exists():
                return False, "FFmpeg reported success, but temp output file was not created."

            #  SUCCESS: Log the stderr because that contains the bitrate/codec info
            # stderr_data = process.stderr.read() if process.stderr else ""
            temp_output_path.rename(output_path)

            return True, f"FFmpeg Output: {stderr_data.strip()}"
        # except subprocess.CalledProcessError as e:
        #     # logger.stream(f"CRITICAL: {str(e)}", fg="red")
        #     return False, f"CRITICAL: {str(e)}"
        except FileNotFoundError as e:
            return (
                False,
                f"CRITICAL: ffmpeg binary not found. Check your AppConfig/PATH. {str(e)}",
            )
        except Exception as e:
            self._cleanup_bad_output(dst=temp_output_path)
            return False, f"CRITICAL: System error: {str(e)}."

    def convert_video_to_apple_safe(
        self,
        file_path: Path,
        target: VideoContainer,
        output_path: Path,
    ) -> tuple[bool, str]:
        video_record = self.probe_service.probe_video(file_path)
        if video_record is None:
            return False, "file can't be converted"
        decision = PolicyDecision()
        policy = PolicyService().get_policy_based_on_video_record(video_record)
        if policy is not None:
            policy.apply(video_record=video_record, decision=decision)
        if target == VideoContainer.MP4:
            target_policy = AppleSafeMp4TargetPolicy()
            target_policy.apply(video_record=video_record, decision=decision)
        builder_service = CommandBuilderService(self.ffmpeg_path, self.logger)
        temp_output = output_path.with_name(
             f"{output_path.stem}.{os.getpid()}.tmp{output_path.suffix}"
        )
        temp_output_path = Path(temp_output)
        args = builder_service.build(
            video_record=video_record, output_path=temp_output_path, decision=decision
        )
        cmd = args

        # logger.regular_log(f"In ConvertService.... decision: {decision}\n")
        # logger.regular_log(f"In ConvertService.... cmd: {cmd}")
        # cmd.insert(1, "-threads")
        # cmd.insert(2, "1")
        # temp output before the conversion completes

        try:
            process = subprocess.Popen(
            # process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr (2>)
                text=True,
                errors="replace",
            )
            # stdout, stderr_data = process.communicate()
            # We wait for the process to finish
            # process.wait()
            # stderr_data = ""
            _, stderr_data = process.communicate()
            stderr_data = stderr_data or ""

            # self.logger.regular_log(f'In ConvertService...pcocess.returncode: {process.returncode}....stderr_data: {stderr_data}')
            if process.returncode != 0:
                # stderr_data = process.stderr.read() if process.stderr else ""
                self._cleanup_bad_output(dst=temp_output_path)
                return (
                    False,
                    f"FFmpeg Error (Code {process.returncode}): {stderr_data.strip()}",
                )

            # SUCCESS: Log the stderr because that contains the bitrate/codec info
            # stderr_data = process.stderr.read() if process.stderr else ""
            # if stderr_data:
            temp_output_path.rename(output_path)
            return True, f"FFmpeg Output: {stderr_data.strip()}"
        except subprocess.CalledProcessError as e:
            # logger.stream(f"CRITICAL: {str(e)}", fg="red")
            return False, f"CRITICAL: {str(e)}"
        except FileNotFoundError as e:
            return (
                False,
                f"CRITICAL: {str(e)}",
            )
        except Exception as e:
            self._cleanup_bad_output(dst=temp_output_path)
            return False, f"CRITICAL: System error: {str(e)}"

    def convert_task_wrapper(self, task_data: ConversionTask) -> ConversionTaskResult:
        """
        Unpacks the ConversionTask and returns ConvesionTaskResult.

        """
        file_path = task_data.file_path
        target = task_data.target
        output_path = task_data.output_path
        success = False
        msg = ""
        if isinstance(target, AudioFormat):
            bit_rate = task_data.bitrate
            success, msg = self.convert_flac_to_apple_friendly(
                file_path,
                target,
                output_path,
                bit_rate,
            )
        elif isinstance(target, VideoContainer):
            success, msg = self.convert_video_to_apple_safe(
                file_path=file_path,
                target=target,
                output_path=output_path,
            )

        return ConversionTaskResult(
            file_path=file_path,
            output_path=task_data.output_path,
            success=success,
            message=msg,
        )
    
    # helper function to delete output that is bad
    def _cleanup_bad_output(self, dst: Path | None) -> None:
        if dst is None:
            return
        try:
            # if dst.exists():
            dst.unlink(missing_ok=True)
        except OSError:
            pass

    def run_parallel_conversion(
        self,
        all_tasks: list[ConversionTask],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[ConversionTaskResult]:
        """
        The main engine driver.
        Input: A list of ConversionTask dictionaries.
        Output: A list of results (path, success, message).
        """
        results: list[ConversionTaskResult] = []
        max_workers = max(1, (os.cpu_count() or 4) - 1)
        # this following is a setup for I/O bound while converison is cpu intensive.

        total = len(all_tasks)
        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks at once
            future_to_path = {
                executor.submit(self.convert_task_wrapper, task): task.file_path
                for task in all_tasks
            }

            for future in as_completed(future_to_path):
                task_result = future.result()
                results.append(task_result)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                # bar.update(1)  # This makes the bar move smoothly for every file

        return results
