
from enum import Enum, StrEnum
class AudioFamily(str, Enum):
    LOSSLESS = "lossless"
    LOSSY = "lossy"
    UNKNOWN = "unknown"
