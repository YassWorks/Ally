import argparse
from app.src.config.ui import AgentUI
import sys

class ArgsParser(argparse.ArgumentParser):
    """Parses CLI flags with custom UI error reporting"""

    def __init__(self, ui: AgentUI):
        super().__init__(prog="ally", description="Ally CLI flags")
        self.ui = ui
        self.add_argument(
            "--create-project",
            action="store_true",
            help="Initialize new project workspace",
        )
        self.add_argument(
            "--allow-all-tools",
            action="store_true",
            help="Enable unrestricted tool execution for the session (WARNING: bypasses security)",
        )
        self.add_argument("-d", help="Specify working directory path")
        self.add_argument("-p", help="Initial message/prompt for Ally")

    def error(self, message):
        usage = self.format_help()
        self.ui.error(f"{message}\n{usage}")
        sys.exit(2)

    @classmethod
    def get_args(cls, ui: AgentUI, user_args: list[str] = None) -> argparse.Namespace:
        """Return parsed args using this parser subclass"""
        parser = cls(ui)
        return parser.parse_args(user_args)
