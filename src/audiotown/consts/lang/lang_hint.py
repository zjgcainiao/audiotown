from dataclasses import dataclass

@dataclass(slots=True)
class LangHint:
    prefer: str | None = None          # "cjk", "japanese", "korean", "cyrillic"
    variant: str | None = None         # "simplified", "traditional", or None
    confidence: float = 0.0
    mixed_script: bool = False
