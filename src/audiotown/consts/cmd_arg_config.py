from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass(slots=True)
class CmdArgsConfig:
    cmd_name: str
    dry_run: bool = False
    verbose: bool = False
    report_path: Optional[Path] = None
    bit_rate: int = 0
    find_duplicate: bool = False

    def __init__(self, cmd_name: str):
        self.cmd_name = cmd_name
        self.dry_run = False
        self.report_path = None
        self.bit_rate = 0
        self.find_duplicate = False
        if not self.cmd_name:
            raise ValueError(f"Error A cmmd name is requried.")