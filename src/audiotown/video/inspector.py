from dataclasses import dataclass


@dataclass(slots=True)
class VideoInspector:
    def __init__(self):
        # A map of extension -> Policy Class
        self.policies = {
            ".mkv": MKVPolicy(),
            ".rmvb": RMVBPolicy(),
            ".avi": AVIPolicy()
        }

    def inspect(self, file_path):
        ext = get_extension(file_path)
        probe_data = self.run_ffprobe(file_path)
        
        # Select the correct expert for this file
        policy = self.policies.get(ext, DefaultPolicy())
        
        # The Expert returns a MediaReport (the "Passport" we discussed)
        return policy.evaluate(probe_data)