from abc import ABC, abstractmethod
from audiotown.video.consts import MediaAction

class BaseFormatPolicy(ABC):
    @abstractmethod
    def evaluate(self, probe_data: dict) -> MediaAction:
        """Return the recommended action for this media file."""
        raise NotImplementedError