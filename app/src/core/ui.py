import os
from rich.console import Console
from app.utils.constants import CONSOLE_WIDTH
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.key_binding import KeyBindings
from rich.markdown import Markdown
from rich.prompt import Confirm
from rich.panel import Panel
from rich.text import Text
from typing import Any
from app.utils.constants import THEME
from app.utils.ui_messages import UI_MESSAGES
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
        help_content = UI_MESSAGES["help"]["content"].copy()

        if model_name:
            help_content.append("")
            help_content.append(UI_MESSAGES["help"]["model_suffix"].format(model_name))

        help_content.append(UI_MESSAGES["help"]["footer"])
        markdown_content = Markdown("\n".join(help_content))

        panel = Panel(
            markdown_content,
            title=f"[bold]{UI_MESSAGES['titles']['help']}[/bold]",
            border_style=self._style("muted"),
            padding=(1, 2),
        )
        self.console.print(panel)

    def tool_call(self, tool_name: str, args: dict[str, Any]):
        tool_name = UI_MESSAGES["tool"]["title"].format(tool_name)
        content_parts = [tool_name]
        if args:
            content_parts.append(UI_MESSAGES["tool"]["arguments_header"])
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
            title=f"[bold]{UI_MESSAGES['titles']['tool_executing']}[/bold]",
            border_style=self._style("accent"),
            padding=(1, 2),
        )
        self.console.print(panel)

    def tool_output(self, tool_name: str, content: str):
        tool_name = f"{tool_name}"
        if len(content) > 1000:
            content = content[:1000] + UI_MESSAGES["tool"]["truncated"]

        markdown_content = (
            f"{UI_MESSAGES['tool']['output_header']}\n```\n{content}\n```"
        )

        try:
            rendered_content = Markdown(markdown_content)
        except:
            rendered_content = markdown_content

        self.console.print(
            f"[{self._style('secondary')}]{UI_MESSAGES['tool']['tool_complete'].format(tool_name)}[/{self._style('secondary')}]"
        )
        self.console.print(rendered_content)

    def ai_response(self, content: str):
        try:
            rendered_content = Markdown(content)
        except:
            rendered_content = content

        panel = Panel(
            rendered_content,
            title=f"[bold]{UI_MESSAGES['titles']['assistant']}[/bold]",
            border_style=self._style("primary"),
            padding=(1, 2),
        )
        self.console.print(panel)

    def status_message(self, title: str, message: str, style: str = "primary"):
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
        cwd: str | None = None,
        model: str | None = None,
    ) -> str:
        try:
            info_parts = []
            if cwd:
                info_parts.append(f"[dim]{cwd}[/dim]")
            if model:
                info_parts.append(f"[dim]{model}[/dim]")

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

            # using prompt-toolkit for multiline support
            key_binds = KeyBindings()

            @key_binds.add("c-n")
            def _(event):
                event.current_buffer.insert_text("\n")

            @key_binds.add("enter")
            def _(event):
                event.current_buffer.validate_and_handle()

            result = prompt(">> ", multiline=True, key_bindings=key_binds)
            return result.strip() if result else (default or "")

        except KeyboardInterrupt:
            self.session_interrupted()
            sys.exit(0)
        except Exception as e:
            self.error(str(e))
            return default or ""

    def confirm(self, message: str, default: bool = True) -> bool:
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
                UI_MESSAGES["warnings"]["failed_confirm"].format(
                    "y" if default else "n"
                )
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
        self.status_message(
            title=UI_MESSAGES["titles"]["goodbye"],
            message=UI_MESSAGES["messages"]["goodbye"],
            style="primary",
        )

    def history_cleared(self):
        self.status_message(
            title=UI_MESSAGES["titles"]["history_cleared"],
            message=UI_MESSAGES["messages"]["history_cleared"],
            style="success",
        )

    def session_interrupted(self):
        self.status_message(
            title=UI_MESSAGES["titles"]["interrupted"],
            message=UI_MESSAGES["messages"]["session_interrupted"],
            style="warning",
        )

    def recursion_warning(self):
        panel = Panel(
            UI_MESSAGES["messages"]["recursion_warning"],
            title=f"[bold]{UI_MESSAGES['titles']['extended_session']}[/bold]",
            border_style=self._style("warning"),
            padding=(1, 2),
        )
        self.console.print(panel)

    def warning(self, warning_msg: str):
        self.status_message(
            title=UI_MESSAGES["titles"]["warning"],
            message=f"{warning_msg}",
            style="warning",
        )

    def error(self, error_msg: str):
        self.status_message(
            title=UI_MESSAGES["titles"]["error"],
            message=f"{error_msg}",
            style="error",
        )

    def tmp_msg(self, message: str, duration: int = 2):
        with self.console.status(message):
            time.sleep(duration)


default_ui = AgentUI(Console(width=CONSOLE_WIDTH))
