from dataclasses import dataclass
from pathlib import Path
from audiotown.services.probe_service import ProbeService
from .policies import DefaultPolicy, MKVPolicy,RMVBPolicy,AVIPolicy
from audiotown.video.consts import MediaReport, ProbeSummary
from audiotown.consts import FFmpegConfig

@dataclass(slots=True)
class VideoInspector:
    def __init__(self, probe_service:ProbeService):
        # A map of extension -> Policy Class
        self._policies = {
            ".mkv": MKVPolicy(),
            ".rmvb": RMVBPolicy(),
            ".avi": AVIPolicy()
        }
        self.probe_service = ProbeService(FFmpegConfig().ffprobe_path)

    def inspect_file(self, file_path: Path) -> MediaReport:
            # 1. Run ffprobe (The Scout)
            # probe_data = self._run_ffprobe(file_path)
            probe_data = self.probe_service.get_stream_info()
            
            # 2. Find the Expert (The Brain)
            ext = file_path.suffix.lower()
            policy = self._policies.get(ext, MKVPolicy()) # Default to MKV if unknown
            
            # 3. Get the Decision
            suggested_action = policy.evaluate(probe_data)
            
            # 4. Issue the "Passport"
            return MediaReport(
                file_path=file_path,
                action=suggested_action,
                video_codec=probe_data['streams'][0].get('codec_name', 'unknown'),
                audio_codec=probe_data['streams'][1].get('codec_name', 'unknown'),
                is_apple_ready=(suggested_action == Action.SKIP)
            )

    def _run_ffprobe(self, path):
        # Your existing ffprobe logic goes here
        pass