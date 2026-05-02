from .base_format import BaseFormatPolicy


from audiotown.consts.video import (
    VideoRecord,
    PolicyDecision,
    VideoEncoder,
    VideoCodec,
    MediaAction,
    PixelFormat,
)
from audiotown.consts.video.policy_decision import (
    AudioStreamDecision,
    StreamDecision,
    VideoStreamDecision,
)
from audiotown.consts.audio import AudioFormat, AudioBitRateKbps

class RMVBPolicy(BaseFormatPolicy):
    # def evaluate(self, video_record: VideoRecord) -> MediaAction:
    #     return MediaAction.TRANSCODE

    def apply(self, video_record: VideoRecord, decision: PolicyDecision) -> None:  
        decision.action = MediaAction.TRANSCODE
        decision.ignore_unknown = True
        decision.needs_genpts = True
        decision.repair_notes.append("Legacy RMVB source detected; generating timestamps reconstruction.")

        # fine-grained per stream control
        self._build_video_stream_decisions(video_record=video_record,decision=decision)
        self._build_audio_stream_decisions(video_record=video_record,decision=decision)
        self._build_subtitle_stream_decisions(video_record=video_record,decision=decision)

        # for vi in video_record.video_streams:
        #     is_apple_ready = vi.is_apple_ready
        #     codec_name = vi.codec_name
        #     pixel_format = vi.pix_fmt
        #     stream_codec = (
        #         VideoCodec.from_codec_name(codec_name)
        #         if codec_name is not None
        #         else None
        #     )
        #     stream_encoder = (
        #         VideoEncoder.from_video_codec(stream_codec)
        #         if stream_codec is not None
        #         else None
        #     )
        #     stream_mode = StreamDecision.TRANSCODE
        #     tag = None
        #     if is_apple_ready:
        #         stream_mode = StreamDecision.COPY
        #     else:
        #         stream_mode = StreamDecision.TRANSCODE
        #         if stream_codec not in [VideoCodec.H264, VideoCodec.HEVC]:
        #             stream_codec = VideoCodec.HEVC
        #             stream_encoder = VideoEncoder.LIBX265
        #             tag="hvc1"
        #             # retain pixel_format setting or default to
        #             if pixel_format in [PixelFormat.YUV420P, PixelFormat.YUV420P10LE]:
        #                 pixel_format = pixel_format
        #             else:
        #                 pixel_format = PixelFormat.YUV420P10LE
        #         elif stream_codec == VideoCodec.H264:
        #             stream_encoder = VideoEncoder.LIBX264
        #             pixel_format = PixelFormat.YUV420P
        #             if vi.is_annex_b:
        #                 tag= "avc1"
        #         else:

        #             stream_encoder = VideoEncoder.LIBX265
        #             if pixel_format in [PixelFormat.YUV420P, PixelFormat.YUV420P10LE]:
        #                 pixel_format = pixel_format
        #             else:
        #                 pixel_format = PixelFormat.YUV420P10LE
        #             if vi.codec_tag_string is None or "hvc1" not in vi.codec_tag_string:
        #                 tag="hvc1"
        #     decision.video_stream_decisions.append(
        #         VideoStreamDecision(
        #             stream_index=vi.stream_index or 0,
        #             mode=stream_mode,
        #             codec=stream_codec,
        #             encoder=stream_encoder,
        #             pixel_format=pixel_format,
        #             is_vfr=vi.is_vfr,
        #             target_frame_rate=vi.r_frame_rate,
        #             tag=tag
        #         )
        #     )

        # for au in video_record.audio_streams:
        #     au_decision = StreamDecision.TRANSCODE
        #     au_codec_name = au.codec_name
        #     is_apple_ready = au.is_apple_ready
        #     au_format = (
        #         AudioFormat.from_codec(au_codec_name)
        #         if au_codec_name is not None
        #         else None
        #     )
        #     bitrate = au.bit_rate
        #     if is_apple_ready:
        #         au_decision = StreamDecision.COPY

        #     else:
        #         if au_codec_name is None:
        #             au_format = None
        #             bitrate = None
        #             au_decision = StreamDecision.DROP
                    
        #         elif not au_codec_name in AudioFormat.supported_codecs():
        #             au_decision = StreamDecision.DROP
        #             au_format = None
        #             bitrate = None
        #         else:
        #             au_decision = StreamDecision.TRANSCODE
        #             au_format = AudioFormat.AAC

        #     decision.audio_stream_decisions.append(
        #         AudioStreamDecision(
        #             stream_index=au.stream_index or 0,
        #             mode=au_decision,
        #             audio_format=au_format,
        #             # "192k", #str(round(au.bit_rate or 0/1000)) if au.bit_rate is not None else "192",
        #             bitrate=AudioBitRateKbps.choose_aac_bitrate_kbps_output(
        #                 channels=au.channels, source_bitrate_bps=bitrate
        #             ).value,
        #         )
        #     )