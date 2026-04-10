from dataclasses import dataclass
@dataclass(slots=True)
class LangRepairCandidate:
    byte_recovery: str
    decoder: str
    text: str
    score: float