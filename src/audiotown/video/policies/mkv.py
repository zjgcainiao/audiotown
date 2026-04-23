from audiotown.consts.video.policy_decision import AudioStreamDecision, StreamDecision, VideoStreamDecision
from audiotown.consts.video.video_codec import VideoCodec
from .base_format import BaseFormatPolicy
from audiotown.consts.video import MediaAction, video_encoder
from audiotown.consts.video import VideoRecord, PolicyDecision, VideoEncoder
from audiotown.consts.audio import AudioFormat, AudioBitRateKbps

class MKVPolicy(BaseFormatPolicy):

    def apply(self, video_record: VideoRecord, decision: PolicyDecision) -> None:
        # video = video_record.first_video_stream
        # if not video:
        #     # We don't process files without video streams in this pipeline
        #     return

        # # 1. Evaluate Video Health
        # # This checks for: Codec (H.264), PixFmt (yuv420p), packing (AVCC), and CFR.
        # video_ready = video.is_apple_ready
        
        # if not video_ready:
        #     decision.repair_notes.append(f"MKV Video transcode required: {video.codec_name}")
        #     # If the video is VFR (common in MKVs from handbrake/web-rips), 
        #     # we flag it for repair during the transcode process.
        #     if video.is_vfr:
        #         decision.is_variable_frame_rate = True
        #         decision.target_frame_rate = video.r_frame_rate
        #         decision.repair_notes.append("Fixed Variable Frame Rate issues.")
        
        if not video_record.has_playable_av:
            return None

        all_video_ready = all(vi.is_apple_ready for vi in video_record.video_streams)
        # 2. Evaluate Audio Health (The 'all()' Perfectionist)
        audio_streams = video_record.audio_streams or []
        all_audio_ready = all(a.is_apple_ready for a in audio_streams)
        
        if not all_audio_ready:
            # Most MKVs use AC3, DTS, or FLAC. Apple prefers AAC in MP4.
            decision.repair_notes.append("MKV Audio normalization required (non-AAC detected).")

        # 3. Final Decision: The "Apple-Safe" Verdict
        # We only REMUX if every single A/V stream is already in its final form.
        if all_video_ready and all_audio_ready:
            decision.action = MediaAction.REMUX
            decision.repair_notes.append("High-quality remux: No re-encoding performed.")
        else:
            decision.action = MediaAction.TRANSCODE
            # fine-grained per stream control
            for vi in video_record.video_streams:
                stream_codec = VideoCodec.from_codec_name(vi.codec_name) if vi.codec_name is not None else None
                stream_encoder = VideoEncoder.from_video_codec(stream_codec) if stream_codec is not None else None
                stream_mode = StreamDecision.TRANSCODE if not stream_codec in [VideoCodec.HEVC, VideoCodec.H264] else StreamDecision.COPY
                if stream_mode == StreamDecision.TRANSCODE:
                    stream_codec = VideoCodec.HEVC
                    stream_encoder = VideoEncoder.LIBX265

                decision.video_stream_decisions.append(
                    VideoStreamDecision(
                        stream_index=vi.stream_index or 0,
                        mode=stream_mode,
                        codec= stream_codec,
                        encoder=stream_encoder,
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

            # decision.video_encoder = VideoEncoder.LIBX264
            # if video.codec_name is not None:
            #     video_codec = VideoCodec.from_codec_name(video.codec_name) 
            #     if video_codec:
            #         decision.video_encoder = VideoEncoder.from_video_codec(video_codec)   
            # if not decision.video_encoder: 
            #     decision.video_encoder = VideoEncoder.LIBX265
            # decision.audio_format = AudioFormat.AAC

        # 4. Mandatory Global Standard (Always true for MKV -> MP4 conversion)
        decision.faststart = True