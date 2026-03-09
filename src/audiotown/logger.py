
import datetime
import click
from typing import List, Optional
from dataclasses import dataclass, field
import time

@dataclass
class SessionLogger:
    logs: List[str] = field(default_factory=list)
    time_format: str = "%H:%M:%S"

    def __init__(self):
        self.start_time = time.time()
        self.logs = list()

    def _timestamp(self) -> str:
        return datetime.datetime.now().strftime(self.time_format)

    def log(self, message: str):
        """Store a timestamped message in memory only."""
        clean_message = f"[{self._timestamp()}] {message.strip()}"  
        if clean_message:
            clean_message = clean_message.lstrip().rstrip()
        # Save to memory for the file
        self.logs.append(clean_message)      
    def stream(self, message: str,  fg: Optional[str] = None, 
               bold: bool = False, underline: bool = False,
               err: bool = False, reverse: bool = False, dim: bool = False) -> None:
        """
        Print to terminal (with click.secho) AND store a cleaned version in memory.
        Newlines are preserved for terminal output.
        Whitespace-only messages are not timestamped.
        """
        
        # 1. Handle Newlines: Separate the 'meat' of the message from the whitespace
        stripped_message = message.strip()
        leading_newlines = message[:len(message) - len(message.lstrip())]
        trailing_newlines = message[len(message.rstrip()):]

        if stripped_message:
            ts = self._timestamp()

            formatted_terminal_msg = f"[{ts}] {leading_newlines}{stripped_message}{trailing_newlines}"
            self.logs.append(formatted_terminal_msg)
        else:
            # If it's just a newline or empty space, don't timestamp it
            formatted_terminal_msg = message

        click.secho(message, fg=fg, bold=bold, underline=underline,
                    err=err, reverse=reverse, dim=dim,
                    )
    def get_full_log(self) -> str:
        return "\n".join(self.logs)

logger = SessionLogger()