from __future__ import annotations

import audiotown
import platform
from enum import Enum
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from audiotown.logger import SessionLogger

@dataclass(frozen=True, slots=True)
class MetaContent:
    Software: str = "Audiotown"
    Version: str = field(default=str(audiotown.__version__))
    Timestamp: str = field(default_factory=datetime.now().isoformat)
    User: str = field(default_factory=lambda: Path.home().name)
    Python: str = field(default_factory=platform.python_version)
    OS: str = field(default_factory=platform.platform)

    def to_text(self) -> str:
        """
        Dynamically generates the meta text by iterating over
        the dataclass fields.
        """
        # 1. Convert the dataclass to a dictionary
        data = asdict(self)

        # 2. Create the lines using a List Comprehension
        # We capitalize the key and add a colon for that 'Apple' look
        lines = [
            f"{key.replace('_', ' ').title():<12}: {value}"
            for key, value in data.items()
        ]

        # 3. Join them into one big string
        return "\n".join(lines)