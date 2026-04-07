
# from dataclasses import dataclass

# @dataclass(frozen=True, slots=True)
# class ConversionPreset:
#     name: str
#     output_extension: str
#     container: str
#     audio_encoder: str | None
#     video_encoder: str | None
#     subtitle_mode: str
#     preserve_metadata: bool = True
#     preserve_chapters: bool = True
#     faststart: bool = False



# APPLE_MP4 = ConversionPreset(
#     name="apple_mp4",
#     output_extension=".mp4",
#     container="mp4",
#     audio_encoder="aac",
#     video_encoder="libx264",
#     subtitle_mode="mov_text_or_drop",
#     preserve_metadata=True,
#     preserve_chapters=True,
#     faststart=True,
# )