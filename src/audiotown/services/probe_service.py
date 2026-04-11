import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, List
from audiotown.utils import sanitize_metadata, safe_cast
from audiotown.logger import logger, SessionLogger
from audiotown.consts import AudioFormat, AudioRecord  
from audiotown.consts.probe_result import  ProbeResult
from audiotown.consts.stream_info import  StreamInfo
from audiotown.consts.ffmpeg_config import FFmpegConfig
from audiotown.consts.codec_type import CodecType
from audiotown.consts.video.media_info import MediaInfo
from audiotown.consts.video.video_container import VideoContainer
from audiotown.consts.video import AudioStreamSpec, VideoStreamSpec, SubtitleStreamSpec



class ProbeService:
    def __init__(self, ffprobe_path: str, service_logger: SessionLogger = logger):
        self.ffprobe_path = ffprobe_path
        self.logger = service_logger

    @classmethod
    def from_config(cls, ff_config: FFmpegConfig) -> "ProbeService":
        return cls(ffprobe_path=ff_config.require_ffprobe())

    def get_stream_info(
        self,
        file_path: Path,
    ) -> ProbeResult:
        """Uses 'ffprobe' to inspect the file and find all available streams.
        file_path: a single audio file. Path object.
        returns:
        """

        if not file_path.exists():
            msg = f"{file_path} does not exist"
            self.logger.log(msg)
            return ProbeResult(file_path=file_path, success=False, error=msg)

        if not file_path.is_file():
            msg = f"{file_path} is not a file"
            self.logger.log(msg)
            self.logger.stream(f"{file_path} does not exist or can't be opened", fg="red")
            return ProbeResult(file_path=file_path, success=False, error=msg)
        try: 
            cmd = [
                self.ffprobe_path,
                "-hide_banner",
                "-v",
                "error",
                "-of",
                "json",
                "-show_streams",
                "-show_format",
                "-i",
                str(file_path),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, encoding="utf-8"
            )
        except OSError as e:
            msg = f"Failed to execute ffprobe for {file_path}: {e}"
            self.logger.log(msg)
            return ProbeResult(file_path=file_path, success=False, error=msg)
        
        if result.returncode != 0:
            stderr = result.stderr.strip() or "unknown ffprobe error"
            msg = f"ffprobe failed for {file_path}: {stderr}"
            self.logger.log(msg)
            return ProbeResult(file_path=file_path, success=False, error=msg)

        try:
            raw_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            self.logger.log(f"ffprobe returned invalid JSON for {file_path}")
            msg = f"ffprobe returned invalid JSON for {file_path}: {e}"
            self.logger.log(msg)
            return ProbeResult(file_path=file_path, success=False, error=msg)

        steam_info = StreamInfo.from_ffprobe_json(file=file_path,raw_json=raw_json)
        return ProbeResult(file_path=file_path, success=True, stream_info=steam_info)

    def probe_audio(
        self,
        file_path: Path,
    ) -> Optional[AudioRecord]:
        """
        Takes an file path input and does `ffprobe` probing.
        Returns a AudioRecord instance or None
        """
        if not file_path.exists():
            msg = f"{file_path} does not exist"
            self.logger.log(msg)
            return AudioRecord(file_path=file_path,readable=False, error=msg)
        if not file_path.is_file():
            msg = f"The path is not a file: {file_path}"
            self.logger.log(msg)
            return AudioRecord(file_path=file_path,readable=False, error=msg)
        suffix = file_path.suffix.casefold()
        if not suffix:
            msg = "File has no suffix"
            self.logger.log(msg)
            return AudioRecord(file_path=file_path,readable=False,error=msg)
        if not AudioFormat.is_supported(suffix):
            msg = f"Suffix {suffix} not supported."
            self.logger.log(msg)
            return AudioRecord(file_path=file_path,readable=False, error=msg)

        probe_result = self.get_stream_info(file_path)
        is_readable = True

        if not probe_result.success:
            is_readable = False
            return AudioRecord(
                file_path=file_path,
                readable=False,
                error=probe_result.error,
            )
        data = probe_result.stream_info
        if data is None:
            is_readable = False
            return AudioRecord(file_path=file_path, readable=False, error="Probe returned no stream info")

        # stream = data.streams[0] if data.streams and len(data.streams) > 0 else {}
        stream = next(
            (s for s in data.streams if s.get("codec_type") == CodecType.AUDIO),
            None,
        )
        if stream is None:
            msg = "No audio stream found"
            logger.log(
                msg,
            )
            is_readable = False
            return AudioRecord(file_path=file_path,readable=False, error=msg)
        try:
            format_data = data.format
            if format_data.get("tags"):
                format_tags = {
                    k.lower().strip(): v for k, v in format_data.get("tags", {}).items()
                }
            else:
                format_tags = {}

            # -- internal helper function
            def _cleanse_fields(
                data: dict,
                keys: list[str] | None = None,
            ) -> List[Optional[str]]:
                if keys is None:
                    keys = ["artist", "album", "title", "genre", "year", "track_name"]            

                result: list[Optional[str]] = []

                for key in keys:
                    raw_value = data.get(key)

                    if raw_value is None:
                        result.append(None)
                        continue

                    string = str(raw_value).casefold().strip()
                    if not string:
                        result.append(None)
                        continue

                    cleaned = sanitize_metadata(string)
                    result.append(cleaned if cleaned else None)

                return result

            # 2. extract sample_rate, bits,codec_name, etc
            sample_rate = int(stream.get("sample_rate", 0) or 0)
            raw_bits = int(
                stream.get("bits_per_raw_sample", 0) or stream.get("bits_per_sample", 0)
            )
            channels = int(stream.get("channels", 0))

            s_rate = (
                f"{int(stream.get('sample_rate', 0)) // 1000}kHz"
                if stream.get("sample_rate")
                else "??kHz"
            )
            b_depth = f"{raw_bits} bit" if raw_bits and raw_bits != "0" else "?? bit"

            quality_str = f"{s_rate}/{b_depth}/{channels} bits"


            codec_name = stream.get("codec_name", "")  # actual codec
            duration = float(
                stream.get("duration", 0.00) or format_data.get("duration", 0.00)
            )
            bitrate_bps = stream.get("bit_rate", 0) or format_data.get("bit_rate", 0)
            artist_name, album_name, title_name, genre_name, year_name, track_name = (
                _cleanse_fields(
                    format_tags,
                    ["artist", "album", "title", "genre", "date", "track_name"],
                )
            )
            if artist_name is not None and title_name is not None:
                fingerprint = str(artist_name.casefold() + "_" + title_name.casefold())
            else:
                fingerprint = "_"

            audio_format = AudioFormat.from_codec(codec_name)
            if audio_format is None:
                return AudioRecord(
                    file_path=file_path,
                    audio_format=AudioFormat.from_suffix(file_path.suffix.casefold()),
                    readable=False,
                    error=f"Unsupported or unknown codec: {codec_name}",
                )

            has_embedded_artwork = any(
                s.get("codec_type") == CodecType.VIDEO for s in data.streams
            )
            size_bytes = int(
                format_data.get("size", 0) or file_path.stat().st_size or 0
            )

            record = AudioRecord(
                file_path=file_path,
                audio_format=audio_format,
                bitrate_bps=bitrate_bps,
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
                readable=True,
                fingerprint=fingerprint,
                error=None,
                has_embedded_artwork=has_embedded_artwork,
                track=track_name,
            )

            return record
        except (ValueError, TypeError, OSError) as exc:
            # suffix = AudioFormat.from_suffix(file_path.suffix.casefold())
            return AudioRecord(
                file_path=file_path,
                audio_format=AudioFormat.from_suffix(suffix),
                readable=False,
                error=f"Failed to parse probe data: {exc}",
            )    
        

    def probe_video_file(
        self,
        video_file: Path,
    ) -> Optional[MediaInfo]:
        if not video_file.exists():
            msg = "file does not exist."
            return MediaInfo(file=video_file,is_readable=False, error=msg)
        if not video_file.is_file():
            msg = "path is not a file."
            return MediaInfo(file=video_file,is_readable=False, error=msg)
        data_json = self.get_stream_info(file_path=video_file)
        if not data_json.success:
            return MediaInfo(file=video_file,is_readable=False, error=data_json.error)
        stream_info = data_json.stream_info
        if stream_info is None:
            return MediaInfo(file=video_file,is_readable=False, error="probe returned no stream info.")
        if len(stream_info.streams)==0:
            return MediaInfo(file=video_file,is_readable=False, error="No available streams found.")
        video_streams = [
            s for s in stream_info.streams
            if s.get("codec_type") == CodecType.VIDEO
        ]

        audio_streams = [
            s for s in stream_info.streams
            if s.get("codec_type") == CodecType.AUDIO
        ]

        subtitle_streams = [
            s for s in stream_info.streams
            if s.get("codec_type") == CodecType.SUBTITLE
        ]

        attachment_streams = [
            s for s in stream_info.streams
            if s.get("codec_type") == CodecType.ATTACHMENT
        ]
        video_specs: list[VideoStreamSpec] = []
        audio_specs: list[AudioStreamSpec] = []
        subtitle_specs: list[SubtitleStreamSpec] = []

        for stream in stream_info.streams:
            codec_type = stream.get("codec_type", None)

            if codec_type == CodecType.VIDEO:
                video_specs.append(VideoStreamSpec(
                    stream_index=safe_cast(stream.get("index", None), int),
                    width=safe_cast(stream.get("width"), int),
                    height=safe_cast(stream.get("height"), int),
                    codec_tag_string=safe_cast(stream.get("codec_tag_string"), str),
                    pix_fmt=stream.get("pix_fmt"),
                    bit_rate=safe_cast(stream.get("bit_rate"), int) or None,
                    r_frame_rate=stream.get("r_frame_rate"),
                    avg_frame_rate=stream.get("avg_frame_rate"),
                    duration_sec=safe_cast(stream.get("duration"), float),
                    codec_name=stream.get("codec_name"),
                    profile=stream.get("profile"),
                    level=stream.get("level"),
                    lang=stream.get("tags",{}).get("language",None),
                    is_default=bool(stream.get("disposition", {}).get("default", 0)),
                    is_avc=stream.get("is_avc",None),
                    ))
            elif codec_type == CodecType.AUDIO:
                audio_specs.append(AudioStreamSpec(
                    stream_index=safe_cast(stream.get("index"), int),
                    sample_rate = safe_cast(stream.get("sample_rate"), int),
                    bits_per_sample = safe_cast( stream.get("bits_per_raw_sample") or stream.get("bits_per_sample"), int),
                    codec_name= stream.get("codec_name") or None,
                    bit_rate= safe_cast(stream.get("bit_rate"), int),
                    channels= safe_cast(stream.get("channels"), int),
                    lang=stream.get("tags",{}).get("language",None),
                    is_default=bool(stream.get("disposition", {}).get("default", 0)),

                ))
            elif codec_type == CodecType.SUBTITLE:
                subtitle_specs.append(SubtitleStreamSpec(
                    stream_index=safe_cast(stream.get("index"), int),
                    codec_name = stream.get("codec_name") or None,
                    lang=stream.get("tags",{}).get("language",None),
                    is_default=bool(stream.get("disposition", {}).get("default", 0)),
                    is_forced=bool(stream.get("disposition", {}).get("forced", 0)),
                    title = stream.get("disposition", {}).get("title", None),
                    
                ))
        # later: convert raw dicts into VideoStreamSpec / AudioStreamSpec / SubtitleStreamSpec
        format_data = stream_info.format
        format_name = format_data.get("format_name")
        video_container = VideoContainer.from_format_name(str(format_name))


        nb_streams = int(format_data["nb_streams"]) if format_data.get("nb_streams") else None
        duration_sec = float(format_data["duration"]) if format_data.get("duration") else None
        size_bytes = int(format_data["size"]) if format_data.get("size") else None
        bit_rate = int(format_data["bit_rate"]) if format_data.get("bit_rate") else None
        
        if not video_streams:
            return MediaInfo(
                file=video_file,
                is_readable=False,
                container_name=video_container,
                format_name=format_name,
                nb_streams=nb_streams,
                error="No video stream found.",
                video_streams=video_specs,
                audio_streams=audio_specs,
                subtitle_streams=subtitle_specs,

            )

        return MediaInfo(
            file=video_file,
            container_name=video_container,
            format_name=format_name,
            nb_streams=nb_streams,
            video_streams=video_specs,
            audio_streams=audio_specs,
            subtitle_streams=subtitle_specs,
            duration_sec=duration_sec,
            size_bytes=size_bytes,
            bit_rate=bit_rate,
            is_readable=True,
            error=None,
        )