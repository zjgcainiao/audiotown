from pathlib import Path
from typing import Optional, List
from audiotown.consts import ffmpeg_config
from audiotown.consts.audio_format import AudioFormat
from audiotown.consts.video import (
    PolicyDecision,
    SpeedProfile,
    SubtitleMode,
    SubtitleStreamSpec,
    VideoCodec,
    AudioStreamSpec,
    MediaAction,
)
from dataclasses import dataclass

from audiotown.consts.video.pixel_format_policy import PixelFormatPolicy
from audiotown.consts.video.quality_profile import QualityProfile
from audiotown.consts.video.video_encoder import VideoEncoder
from audiotown.consts.video.video_container import VideoContainer
from audiotown.consts.video.media_info import MediaInfo
from audiotown.consts.video.lang_map import LANGUAGE_MAP
from audiotown.logger import logger, SessionLogger
from typing import Sequence, TypeVar

# generic type placeholer
T = TypeVar("T")

@dataclass(slots=True)
class CommandBuilderOption:
    input_folder: Optional[Path] = None
    output_folder: Optional[Path] = None
    note: Optional[str] = None

class CommandBuilderService:
    def __init__(
        self,
        ffmpeg_path: str,
        logger: SessionLogger = logger,
        # options: CommandBuilderOption,
    ):
        self.ffmpeg_path = ffmpeg_path
        self.logger = logger
        # self.options = options  # Global settings like bitrate, output folder

    def build(
        self, media_info: MediaInfo, output_path: Path, decision: PolicyDecision
    ) -> list[str]:

        argv = [self.ffmpeg_path, "-hide_banner", "-loglevel", "error", "-y"]

        if decision.needs_genpts:
            argv.extend(["-fflags", "+genpts"])

        argv.extend(["-i", str(media_info.file)])

        argv.extend(["-map", "0:v:0"])
        argv.extend(["-map", "0:a?"])
        # argv.extend(["-map", "0:s?"])
        # 3. Processing Logic
        if decision.action == MediaAction.REMUX:
            # LIGHTNING FAST: Just move the data packets
            argv.extend(["-c:v", "copy"])
            argv.extend(["-c:a", "copy"])
            # argv.extend(["-c:s", "copy"])
        else:
            # TRANSCODE: The heavy lifting logic
            if decision.video_encoder:
                argv.extend(["-c:v", decision.video_encoder.value])
            if decision.video_encoder == VideoEncoder.LIBX264:
                argv.extend(self._build_libx264_quality_args(decision))

            # Fixes that only apply during Transcode
            if (
                decision.is_variable_frame_rate
                and decision.target_frame_rate is not None
            ):
                # argv.extend(shlex.split(f"-fps_mode cfr -r {decision.target_frame_rate}"))
                argv.extend(["-fps_mode", "cfr", "-r", f"{decision.target_frame_rate}"])

            if decision.ignore_unknown:
                argv.append("-ignore_unknown")

            argv.extend(["-tag:v", "avc1"])

            audio_format = decision.audio_format
            if audio_format:
                argv.extend(["-c:a", audio_format.encoder])
                if audio_format.codec_name == AudioFormat.AAC.codec_name:
                    argv.extend(["-b:a", "192k"])

            # Subtitle Mapping: Only map what we can actually handle
            sub_streams = (
                media_info.subtitle_streams if media_info.has_subtitles else []
            )
            eligible_subs = [s for s in sub_streams if s.is_mp4_text_compatible]

            if (
                len(eligible_subs) > 0
                and decision.subtitle_mode == SubtitleMode.MOV_TEXT_OR_DROP
            ):
                # Instead of -map 0:s?, we map specifically the ones that fit our policy
                for stream in eligible_subs:
                    argv.extend(["-map", f"0:{stream.stream_index}"])

                # Now this global flag is SAFE because we only mapped compatible streams
                argv.extend(["-c:s", "mov_text"])
            else:
                # If no text-compatible subs, we don't map any (the 'DROP' part of your policy)
                pass

        argv.extend(
            self._apply_language_and_default_preferences(
                media=media_info, decision=decision
            )
        )
        if decision.faststart:
            argv.extend(["-movflags", "+faststart"])
        # override
        argv.append(str(output_path))
        return argv

    def _build_libx264_quality_args(self, decision: PolicyDecision) -> list[str]:
        args = []

        # 1. Handle Preset
        preset = decision.speed_profile.value if decision.speed_profile else "medium"
        args.extend(["-preset", preset])

        # 2. Handle CRF (Quality)
        # Using a map is cleaner than a chain of if/elifs
        crf_map = {
            QualityProfile.HIGH: 18,
            QualityProfile.BALANCED: 22,
            QualityProfile.LOW: 26,
        }
        crf_value = (
            crf_map.get(decision.quality_profile, 22)
            if decision.quality_profile is not None
            else 22
        )
        args.extend(["-crf", str(crf_value)])

        # 3. Handle Pixel Format
        if decision.pixel_format_policy == PixelFormatPolicy.YUV420P_SAFE:
            args.extend(["-pix_fmt", f"{PixelFormatPolicy.YUV420P_SAFE}"])

        # Safe to have. These ensure the H.264 stream doesn't use features too complex for Apple hardware
        args.extend(["-profile:v", "high", "-level", "4.1"])

        return args

    def _generate_output_path(
        self,
        media: MediaInfo,
        output_folder: Path,
        target_container: VideoContainer = VideoContainer.MP4,
    ) -> str | None:
        # Logic to swap .rmvb/.avi for .mp4 in the target folder

        return str(output_folder / media.file.with_suffix(target_container.suffix).name)

    def _normalize_lang(self, lang: str | None) -> str | None:
        if not lang:
            return None

        lang = lang.strip().lower()

        return LANGUAGE_MAP.get(lang, lang)

    def _find_preferred_english_stream(self, streams: Sequence[T]) -> int | None:
        """
        Returns the index *within the provided list* of the best English stream,
        or None if no English stream exists.
        Preference:
        1. English stream already marked default
        2. First English stream
        """
        # 1. Identify all candidates (Good for future development)
        english_indexes = [
            i
            for i, s in enumerate(streams)
            if self._normalize_lang(getattr(s, "language", None)) == "eng"
        ]

        if not english_indexes:
            return None

        # 2. Apply business logic to the candidates
        # Check if any candidate is the 'default'
        for i in english_indexes:
            if getattr(streams[i], "is_default", False):
                return i

        # 3. Fallback to the first candidate
        return english_indexes[0]

    def _build_default_disposition_args(
        self,
        stream_type: str,  # "a" or "s"
        stream_count: int,
        default_output_index: int | None,
    ) -> List[str]:
        """
        Builds ffmpeg disposition args for output streams of a given type.
        Clears existing defaults and sets exactly one default when requested.
        """
        args: list[str] = []

        if default_output_index is None:
            return args

        for out_idx in range(stream_count):
            args += [f"-disposition:{stream_type}:{out_idx}", "0"]

        args += [f"-disposition:{stream_type}:{default_output_index}", "default"]
        return args

    def _build_language_metadata_args(
        self,
        stream_type: str,  # "a" or "s"
        streams: Sequence,
        english_output_indexes: set[int] | None = None,
        only_fill_missing: bool = True,
    ) -> list[str]:
        """
        Build ffmpeg per-stream language metadata args in a gentle way.

        Rules:
        - Never overwrite an existing non-empty language tag when only_fill_missing=True
        - Only write `language=eng` for streams explicitly identified as English
        - Use output stream indexes, not original input indexes
        """
        args: list[str] = []
        english_output_indexes = english_output_indexes or set()

        for out_idx, stream in enumerate(streams):
            original_lang = getattr(stream, "language", None)
            normalized_lang = self._normalize_lang(original_lang)

            # Gentle mode: keep any existing language tag
            if only_fill_missing and original_lang and str(original_lang).strip():
                continue

            # Only fill when we have a confident inference
            if out_idx in english_output_indexes:
                target_lang = "eng"
            else:
                # No confident inference -> leave missing as missing
                continue

            # Avoid writing if normalization already resolves to the same value
            if (
                normalized_lang == target_lang
                and original_lang
                and str(original_lang).strip()
            ):
                continue

            args += [f"-metadata:s:{stream_type}:{out_idx}", f"language={target_lang}"]

        return args

    # Main builder integration
    def _apply_language_and_default_preferences(
        self,
        # args: list[str],
        media: MediaInfo,
        decision: PolicyDecision,
    ) -> list[str]:
        args: list[str] = []
        # Audio default preference
        output_audio_streams = media.audio_streams
        output_subtitle_streams = media.subtitle_streams

        if decision.prefer_english_audio_default:
            preferred_audio_idx = self._find_preferred_english_stream(
                output_audio_streams
            )
            args.extend(
                self._build_default_disposition_args(
                    stream_type="a",
                    stream_count=len(output_audio_streams),
                    default_output_index=preferred_audio_idx,
                )
            )
            if preferred_audio_idx is not None:
                decision.repair_notes.append("Set English audio as default.")

        # Subtitle default preference
        if decision.prefer_english_subtitle_default:
            preferred_sub_idx = self._find_preferred_english_stream(
                output_subtitle_streams
            )
            args.extend(
                self._build_default_disposition_args(
                    stream_type="s",
                    stream_count=len(output_subtitle_streams),
                    default_output_index=preferred_sub_idx,
                )
            )
            if preferred_sub_idx is not None:
                decision.repair_notes.append("Set English subtitle as default.")

        # Optional metadata normalization
        if decision.normalize_missing_language_tags:
            args.extend(
                self._build_language_metadata_args(
                    stream_type="a",
                    streams=output_audio_streams,
                    only_fill_missing=True,
                )
            )
            args.extend(
                self._build_language_metadata_args(
                    stream_type="s",
                    streams=output_subtitle_streams,
                    only_fill_missing=True,
                )
            )

        return args
