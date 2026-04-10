from dataclasses import dataclass

@dataclass(slots=True)
class LangTextQuality:
    score: float
    suspicious: bool
    reasons: list[str]