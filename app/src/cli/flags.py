import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

from app.src.core.ui import AgentUI
from app.utils.logger import logger


class ArgsParser(argparse.ArgumentParser):
    """Command-line flags for ``ally``, with errors reported through the UI."""

    def __init__(self, ui: AgentUI):
        super().__init__(
            prog="ally", description="Ally: an AI agent for your terminal."
        )
        self.ui = ui
        self.add_argument(
            "--version", action="version", version=f"%(prog)s {_installed_version()}"
        )
        self.add_argument(
            "--create-project",
            action="store_true",
            help="start the project generation workflow",
        )
        self.add_argument(
            "--allow-all-tools",
            action="store_true",
            help="run every tool without asking for permission (use with care)",
        )
        self.add_argument(
            "-d", "--dir", dest="d", metavar="DIR", help="working directory"
        )
        self.add_argument(
            "-p", "--prompt", dest="p", metavar="PROMPT", help="first message to send"
        )
        self.add_argument(
            "-i",
            "--id",
            dest="i",
            metavar="ID",
            help="session ID to resume (see /id inside a chat)",
        )

    def error(self, message):
        logger.error(f"Argument parsing error: {message}")
        self.ui.error(f"{message}\n{self.format_usage()}")
        sys.exit(2)

    @classmethod
    def get_args(
        cls, ui: AgentUI, user_args: list[str] | None = None
    ) -> argparse.Namespace:
        """Parse ``user_args`` with this parser."""
        return cls(ui).parse_args(user_args)


def _installed_version() -> str:
    try:
        return version("ally")
    except PackageNotFoundError:
        return "unknown"
