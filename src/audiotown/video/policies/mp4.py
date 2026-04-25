from .base_format import BaseFormatPolicy
from audiotown.consts.video.pixel_format_policy import PixelFormat
from audiotown.consts.video import VideoRecord, PolicyDecision, MediaAction, VideoEncoder, VideoCodec, StreamDecision, VideoStreamDecision, AudioStreamDecision
from audiotown.consts.audio import AudioFormat, AudioBitRateKbps
from audiotown.logger import logger

class MP4Policy(BaseFormatPolicy):
    def apply(self, video_record: VideoRecord, decision: PolicyDecision) -> None:
    
        if not video_record.has_playable_av:
            return None

        all_video_ready = all(vi.is_apple_ready for vi in video_record.video_streams)
        # 2. Evaluate Audio Health (The 'all()' Perfectionist)
        audio_streams = video_record.audio_streams or []
        all_audio_ready = all(a.is_apple_ready for a in audio_streams)
        
        if not all_audio_ready:
            # Most MKVs use AC3, DTS, or FLAC. Apple prefers AAC in MP4.
            decision.repair_notes.append("MP4 Audio normalization required (non-AAC detected).")

        # 3. Final Decision: The "Apple-Safe" Verdict
        # We only REMUX if every single A/V stream is already in its final form.
        if all_video_ready and all_audio_ready:
            decision.action = MediaAction.SKIP
            decision.repair_notes.append("Mp4 ready for direct play: No action performed.")
            for vi in video_record.video_streams:
                
                stream_codec = VideoCodec.from_codec_name(vi.codec_name) if vi.codec_name is not None else None
                stream_encoder = VideoEncoder.from_video_codec(stream_codec) if stream_codec is not None else None
                pixel_format = vi.pix_fmt
                stream_mode = StreamDecision.COPY if stream_codec in [VideoCodec.HEVC, VideoCodec.H264] else StreamDecision.TRANSCODE
                VideoStreamDecision(
                        stream_index=vi.stream_index or 0,
                        mode=stream_mode,
                        codec= stream_codec,
                        encoder=stream_encoder,
                        pixel_format=pixel_format,
                        is_vfr=vi.is_vfr,
                        target_frame_rate=vi.r_frame_rate

                    )

        else:
            decision.action = MediaAction.TRANSCODE
            # fine-grained per stream control
            for vi in video_record.video_streams:
                pixel_format = vi.pix_fmt
                stream_codec = VideoCodec.from_codec_name(vi.codec_name) if vi.codec_name is not None else None
                stream_encoder = VideoEncoder.from_video_codec(stream_codec) if stream_codec is not None else None
                stream_mode = StreamDecision.COPY if stream_codec in [VideoCodec.HEVC, VideoCodec.H264] else StreamDecision.TRANSCODE
                if stream_mode == StreamDecision.TRANSCODE:
                    if stream_codec == VideoCodec.H264:
                        stream_encoder = VideoEncoder.LIBX264
                        pixel_format = PixelFormat.YUV420P
                    if stream_codec == VideoCodec.HEVC:
                        stream_encoder = VideoEncoder.LIBX265
                        if pixel_format in [PixelFormat.YUV420P,PixelFormat.YUV420P10LE]:
                            pixel_format = pixel_format
                        else:
                            pixel_format = PixelFormat.YUV420P10LE
                    if stream_codec not in [VideoCodec.H264, VideoCodec.HEVC]:
                        stream_codec = VideoCodec.HEVC
                        stream_encoder = VideoEncoder.LIBX265
                        if pixel_format in [PixelFormat.YUV420P,PixelFormat.YUV420P10LE]:
                            pixel_format = pixel_format
                        else:
                            pixel_format = PixelFormat.YUV420P10LE
                # now check the pixel_format concistency
                decision.video_stream_decisions.append(
                    VideoStreamDecision(
                        stream_index=vi.stream_index or 0,
                        mode=stream_mode,
                        codec= stream_codec,
                        encoder=stream_encoder,
                        pixel_format=pixel_format,
                        is_vfr=vi.is_vfr,
                        target_frame_rate=vi.r_frame_rate

                    )
                )
            for au in video_record.audio_streams:
                au_decision = StreamDecision.TRANSCODE
                au_codec_name = au.codec_name
                au_format = AudioFormat.from_codec(au_codec_name) if au_codec_name is not None else None
                if au_codec_name is None:
                    au_format = None
                    au_decision = StreamDecision.DROP
                if not au_codec_name in AudioFormat.supported_codecs():
                    au_decision = StreamDecision.DROP
                    au_format = None
                if au_format is not None and au_format in [AudioFormat.AAC]:
                    au_decision =StreamDecision.COPY
                else:
                    au_decision =StreamDecision.TRANSCODE
                    au_format = AudioFormat.AAC
                
                decision.audio_stream_decisions.append(
                    AudioStreamDecision(
                        stream_index=au.stream_index or 0,
                        mode = au_decision,
                        audio_format= au_format,
                        #"192k", #str(round(au.bit_rate or 0/1000)) if au.bit_rate is not None else "192",
                        bitrate= AudioBitRateKbps.choose_aac_bitrate_kbps_output(channels=au.channels,source_bitrate_bps=au.bit_rate).value ,
                    )
                )

            # disable the high level use of `video_codec` and `video_encoder` and `audio_format`.
            # REPLY on `video_stream_decisions` and `audio_stream_decisiobs` to do fine-grained control
            decision.video_codec = None
            decision.video_encoder = None
            decision.audio_format = None
            decision.is_variable_frame_rate = False
            decision.target_frame_rate = None
        # 4. Mandatory Global Standard (Always true for MKV -> MP4 conversion)
            decision.faststart = True

            logger.regular_log(f"here is the edn of MP4 Policy. show me the decision: {decision}")