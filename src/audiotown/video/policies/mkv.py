from .base_format import BaseFormatPolicy
from audiotown.video.consts import MediaAction


class MKVPolicy(BaseFormatPolicy):
    def evaluate(self, probe_data: dict) -> MediaAction:
        v_codec = probe_data['streams'][0].get('codec_name', '')
        a_codec = probe_data['streams'][1].get('codec_name', '')
        
        # The "Customs Officer" Check
        if v_codec in ['h264', 'hevc'] and a_codec in ['aac', 'alac', 'mp3']:
            return MediaAction.REMUX  # Fast path
        return MediaAction.TRANSCODE  # Heavy path
