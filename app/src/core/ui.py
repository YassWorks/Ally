import os
from rich.console import Console
from app.utils.constants import CONSOLE_WIDTH
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from typing import Any
from app.utils.constants import THEME
import time
import sys

if os.name == "nt":
    import msvcrt
else:
    import tty
    import termios


class AgentUI:

    def __init__(self, console: Console):
        self.console = console

    def _style(self, color_key: str) -> str:
        return THEME.get(color_key, THEME["text"])

    def logo(self, ascii_art: str):
        self.console.print()
        lines = ascii_art.split("\n")
        for i, line in enumerate(lines):
            progress = i / max(len(lines) - 1, 1)
            red = int(139 + (239 - 139) * progress)
            green = int(92 + (68 - 92) * progress)
            blue = int(246 + (68 - 246) * progress)

            color = f"#{red:02x}{green:02x}{blue:02x}"
            text = Text(line, style=f"bold {color}")
            self.console.print(text)

    def help(self, model_name: str = None):
        self.console.print()
        help_content = []
        help_content.append("Chat with your AI assistant")
        help_content.append("")
        help_content.append("Commands:")
        help_content.append("  /quit, /exit, /q  → Exit")
        help_content.append("  /clear            → Clear history*")
        help_content.append("  /cls              → Clear screen")

        if model_name:
            help_content.append("")
            help_content.append(f"Model: [bold]{model_name}[/bold]")

        help_content.append(
            "\n[italic][dim](*Not recommended during long running tasks. Use at your own risk.)[/dim][/italic]"
        )

        panel = Panel(
            "\n".join(help_content),
            title="[bold]Help[/bold]",
            border_style=self._style("muted"),
            padding=(1, 2),
        )
        self.console.print(panel)

    def tool_call(self, tool_name: str, args: dict[str, Any]):
        self.console.print()

        tool_name = f"## {tool_name}"
        content_parts = [tool_name]
        if args:
            content_parts.append("\n**Arguments:**")
            for k, v in args.items():

                value_str = str(v)
                if len(value_str) > 100 or "\n" in value_str:
                    content_parts.append(
                        f"- **{k}:**\n```\n{value_str[:500]}{'...' if len(value_str) > 500 else ''}\n```"
                    )
                else:
                    content_parts.append(f"- **{k}:** `{value_str}`")

        markdown_content = "\n".join(content_parts)

        try:
            rendered_content = Markdown(markdown_content)
        except:
            rendered_content = markdown_content

        panel = Panel(
            rendered_content,
            title="[bold]Tool Executing[/bold]",
            border_style=self._style("accent"),
            padding=(1, 2),
        )
        self.console.print(panel)

    def tool_output(self, tool_name: str, content: str):
        self.console.print()

        tool_name = f"{tool_name}"
        if len(content) > 1000:
            content = content[:1000] + "\n... *(truncated)*"

        markdown_content = f"**Output:**\n```\n{content}\n```"

        try:
            rendered_content = Markdown(markdown_content)
        except:
            rendered_content = markdown_content

        self.console.print(
            f"[{self._style('secondary')}]Tool Complete: {tool_name}[/{self._style('secondary')}]"
        )
        self.console.print(rendered_content)

    def ai_response(self, content: str):
        self.console.print()
        try:
            rendered_content = Markdown(content)
        except:
            rendered_content = content

        panel = Panel(
            rendered_content,
            title="[bold]Assistant[/bold]",
            border_style=self._style("primary"),
            padding=(1, 2),
        )
        self.console.print(panel)

    def status_message(self, title: str, message: str, style: str = "primary"):
        self.console.print()
        panel = Panel(
            message,
            title=f"[bold]{title}[/bold]",
            border_style=self._style(style),
            padding=(0, 1),
        )
        self.console.print(panel)

    def get_input(
        self,
        message: str = None,
        default: str | None = None,
        password: bool = False,
        choices: list[str] | None = None,
        show_choices: bool = False,
        cwd: str | None = None,
        model: str | None = None,
    ) -> str:
        self.console.print()
        try:
            info_parts = []
            if cwd:
                info_parts.append(f"[dim]📂 {cwd}[/dim]")
            if model:
                info_parts.append(f"[dim]🤖 {model}[/dim]")

            info_line = " • ".join(info_parts) if info_parts else ""

            prompt_content = message or ""
            if default:
                prompt_content += f" [dim](default: {default})[/dim]"

            if info_line:
                prompt_content += (
                    f"\n{info_line}" if prompt_content.strip() else info_line
                )

            panel = Panel(
                prompt_content, border_style=self._style("border"), padding=(0, 1)
            )
            self.console.print(panel)

            kwargs = {"console": self.console, "show_default": False}
            if default is not None:
                kwargs["default"] = default
            if password:
                kwargs["password"] = True
            if choices:
                kwargs["choices"] = choices

            return Prompt.ask(">>", **kwargs)
        except Exception as e:
            self.error(str(e))
            return default or ""

    def confirm(self, message: str, default: bool = True) -> bool:
        self.console.print()
        try:
            panel = Panel(message, border_style=self._style("warning"), padding=(0, 1))
            self.console.print(panel)
            return Confirm.ask(
                ">>", default=default, console=self.console, show_default=False
            )
        except KeyboardInterrupt:
            self.session_interrupted()
            sys.exit(0)
        except Exception:
            self.warning(
                f"Failed to confirm action. Continuing with default value ({'y' if default else 'n'})"
            )
            return default

    def get_key(self):
        """Read a single key press and return a string identifier."""
        if os.name == "nt":
            key = msvcrt.getch()
            if key == b"\xe0":  # Special keys (arrows, F keys, etc.)
                key = msvcrt.getch()
                return {
                    b"H": "UP",
                    b"P": "DOWN",
                }.get(key, None)
            elif key in (b"\r", b"\n"):
                return "ENTER"
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch1 = sys.stdin.read(1)
                if ch1 == "\x1b":  # Escape sequence
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        return {
                            "A": "UP",
                            "B": "DOWN",
                        }.get(ch3, None)
                elif ch1 in ("\r", "\n"):
                    return "ENTER"
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None

    def select_option(self, message: str, options: list[str]) -> int:
        idx = 0
        self.console.print(f"\n{message}")
        for i, opt in enumerate(options):
            prefix = "▶ " if i == idx else "  "
            print(f"{prefix}{opt}")

        while True:
            key = self.get_key()
            if key == "UP" and idx > 0:
                idx -= 1
            elif key == "DOWN" and idx < len(options) - 1:
                idx += 1
            elif key == "ENTER":
                return idx

            # Move cursor up to menu start
            sys.stdout.write(f"\033[{len(options)}A")
            for i, opt in enumerate(options):
                prefix = "▶ " if i == idx else "  "
                sys.stdout.write(f"{prefix}{opt}\033[K\n")
            sys.stdout.flush()

    def goodbye(self):
        self.console.print()
        self.status_message(
            title="Goodbye",
            message="Thanks for using the assistant!",
            style="primary",
        )

    def history_cleared(self):
        self.console.print()
        self.status_message(
            title="History Cleared",
            message="Conversation history cleared",
            style="success",
        )

    def session_interrupted(self):
        self.console.print()
        self.status_message(
            title="Interrupted",
            message="Session interrupted by user",
            style="warning",
        )

    def recursion_warning(self):
        self.console.print()
        content = (
            "Agent has been processing for a while.\nContinue or refine your prompt?"
        )
        panel = Panel(
            content,
            title="[bold]Extended Session[/bold]",
            border_style=self._style("warning"),
            padding=(1, 2),
        )
        self.console.print(panel)

    def warning(self, warning_msg: str):
        self.console.print()
        self.status_message(
            title="Warning",
            message=f"{warning_msg}",
            style="warning",
        )

    def error(self, error_msg: str):
        self.console.print()
        self.status_message(
            title="Error",
            message=f"{error_msg}",
            style="error",
        )

    def tmp_msg(self, message: str, duration: int = 2):
        self.console.print()
        with self.console.status(message):
            time.sleep(duration)


default_ui = AgentUI(Console(width=CONSOLE_WIDTH))
