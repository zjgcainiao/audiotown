from abc import ABC, abstractmethod
from audiotown.consts import video
from audiotown.consts.video import VideoRecord, PolicyDecision, MediaAction, VideoEncoder, VideoCodec, StreamDecision, VideoStreamDecision, AudioStreamDecision, VideoStreamSpec, AudioStreamSpec, PixelFormat
from audiotown.consts.video.policy_decision import AudioStreamDecision, StreamDecision, SubtitleStreamDecision, VideoStreamDecision
from audiotown.consts.audio import AudioFormat, AudioBitRateKbps
from audiotown.consts.video.subtitle_mode import SubtitleMode



class BaseFormatPolicy(ABC):
    # @abstractmethod
    # def evaluate(self, probe_data: dict) -> MediaAction:
    #     """Return the recommended action for this media file."""
    #     raise NotImplementedError
    
    @abstractmethod
    def apply(self, video_record: VideoRecord, decision: PolicyDecision) -> None:
        # raise NotImplementedError
        ...


    def _video_streams(self, video_record: VideoRecord) -> list[VideoStreamSpec]:
        return video_record.video_streams if video_record.has_video else []
    
    def _build_video_stream_decisions(self, video_record:VideoRecord, decision: PolicyDecision) -> None:
        if not video_record.has_video:
            decision.video_stream_decisions=[]
            return
        
        for vi in video_record.video_streams:
            is_apple_ready = vi.is_apple_ready
            codec_name = vi.codec_name
            pixel_format = vi.pix_fmt
            stream_codec = (
                VideoCodec.from_codec_name(codec_name)
                if codec_name is not None
                else None
            )
            stream_encoder = (
                VideoEncoder.from_video_codec(stream_codec)
                if stream_codec is not None
                else None
            )
            stream_mode = StreamDecision.TRANSCODE
            tag = None
            if is_apple_ready:
                stream_mode = StreamDecision.COPY
            else:
                stream_mode = StreamDecision.TRANSCODE
                if stream_codec not in [VideoCodec.H264, VideoCodec.HEVC]:
                    stream_codec = VideoCodec.HEVC
                    stream_encoder = VideoEncoder.LIBX265
                    tag="hvc1"
                    # retain pixel_format setting or default to
                    if pixel_format in [PixelFormat.YUV420P, PixelFormat.YUV420P10LE]:
                        pixel_format = pixel_format
                    else:
                        pixel_format = PixelFormat.YUV420P10LE
                elif stream_codec == VideoCodec.H264:
                    stream_encoder = VideoEncoder.LIBX264
                    pixel_format = PixelFormat.YUV420P
                    if vi.is_annex_b:
                        tag= "avc1"
                else:

                    stream_encoder = VideoEncoder.LIBX265
                    if pixel_format in [PixelFormat.YUV420P, PixelFormat.YUV420P10LE]:
                        pixel_format = pixel_format
                    else:
                        pixel_format = PixelFormat.YUV420P10LE
                    if vi.codec_tag_string is None or "hvc1" not in vi.codec_tag_string:
                        tag="hvc1"
            decision.video_stream_decisions.append(
                VideoStreamDecision(
                    stream_index=vi.stream_index or 0,
                    mode=stream_mode,
                    codec=stream_codec,
                    encoder=stream_encoder,
                    pixel_format=pixel_format,
                    is_vfr=vi.is_vfr,
                    target_frame_rate=vi.r_frame_rate,
                    tag=tag
                )
            )

    def _build_audio_stream_decisions(self, video_record:VideoRecord, decision: PolicyDecision) -> None:
        if not video_record.has_audio:
            decision.audio_stream_decisions = []
            return

        for au in video_record.audio_streams:
            au_decision = StreamDecision.TRANSCODE
            au_codec_name = au.codec_name
            is_apple_ready = au.is_apple_ready
            au_format = (
                AudioFormat.from_codec(au_codec_name)
                if au_codec_name is not None
                else None
            )
            bitrate = au.bit_rate
            if is_apple_ready:
                au_decision = StreamDecision.COPY

            else:
                if au_codec_name is None:
                    au_format = None
                    bitrate = None
                    au_decision = StreamDecision.DROP
                    
                elif not au_codec_name in AudioFormat.supported_codecs():
                    au_decision = StreamDecision.DROP
                    au_format = None
                    bitrate = None
                else:
                    au_decision = StreamDecision.TRANSCODE
                    au_format = AudioFormat.AAC

            decision.audio_stream_decisions.append(
                AudioStreamDecision(
                    stream_index=au.stream_index or 0,
                    mode=au_decision,
                    audio_format=au_format,
                    # "192k", #str(round(au.bit_rate or 0/1000)) if au.bit_rate is not None else "192",
                    bitrate=AudioBitRateKbps.choose_aac_bitrate_kbps_output(
                        channels=au.channels, source_bitrate_bps=bitrate
                    ).value,
                )
            )
    def _build_subtitle_stream_decisions(self, video_record:VideoRecord, decision: PolicyDecision) -> None:
        if not video_record.has_subtitle:
            decision.subtitle_stream_decisions=[]
            return
        # default is to drop subtitle
        for sub in video_record.subtitle_streams:
            decision.subtitle_stream_decisions.append(
                SubtitleStreamDecision(
                    stream_index=sub.stream_index or 0,
                    mode=SubtitleMode.DROP,
                    make_default=False
                )
            )
    
    def _validate_final_result(self,video_record:VideoRecord, decision:PolicyDecision):
        pass