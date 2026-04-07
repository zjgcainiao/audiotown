import datetime
import click
from typing import List, Optional
import time
import logging


class SessionLogger:

    def __init__(
        self, time_format: str = "%H:%M:%S", logger: Optional[logging.Logger] = None
    ) -> None:
        self.start_time = time.time()
        self.logs: list[str] = []
        self.time_format = time_format
        self.logger = logger or logging.getLogger(__name__)

    def _timestamp(self) -> str:
        return datetime.datetime.now().strftime(self.time_format)

    def regular_log(self, message: str, level: int = logging.INFO) -> None:

        """Store a timestamped message in memory only."""
        clean = f"[{self._timestamp()}] {message.strip()}"
        if clean:
            clean= clean.lstrip().rstrip()
        # self.logger.info(clean)
        self.logger.log(level, clean)
    def log(self, message: str):
        """Store a timestamped message in memory only."""
        clean = f"[{self._timestamp()}] {message.strip()}"
        if clean:
            clean= clean.lstrip().rstrip()
        self.logs.append(clean)

    def error(self, message: str):
        """Store a timestamped message in memory only."""
        clean_message = f"[{self._timestamp()}] {message.strip()}"
        if clean_message:
            clean_message = clean_message.lstrip().rstrip()

        self.logger.error(clean_message)
        self.logs.append(clean_message)

    def stream(
        self,
        message: str,
        fg: Optional[str] = None,
        bold: bool = False,
        underline: bool = False,
        err: bool = False,
        reverse: bool = False,
        dim: bool = False,
    ) -> None:
        """
        Print to terminal (with click.secho) AND store a cleaned version in memory.
        Newlines are preserved for terminal output.
        Whitespace-only messages are not timestamped.
        """

        # 1. Handle Newlines: Separate the 'meat' of the message from the whitespace
        stripped_message = message.strip()
        leading_newlines = message[: len(message) - len(message.lstrip())]
        trailing_newlines = message[len(message.rstrip()) :]

        if stripped_message:
            ts = self._timestamp()

            formatted_terminal_msg = (
                f"[{ts}] {leading_newlines}{stripped_message}{trailing_newlines}"
            )
            self.logs.append(formatted_terminal_msg)
        else:
            # If it's just a newline or empty space, don't timestamp it
            formatted_terminal_msg = message

        click.secho(
            message,
            fg=fg,
            bold=bold,
            underline=underline,
            err=err,
            reverse=reverse,
            dim=dim,
        )

    def get_full_log(self) -> str:
        return "\n".join(self.logs)


logger = SessionLogger()
