from dataclasses import dataclass
from .media_action import MediaAction

@dataclass(slots=True)
class PolicyDecision:
    action: MediaAction
    is_apple_ready: bool
    description: str