import sys
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich import box
from prompt_toolkit.shortcuts import prompt, choice
from prompt_toolkit.key_binding import KeyBindings
from rich.prompt import Confirm
from typing import Any

from app.utils.constants import CONSOLE_WIDTH, THEME
from app.utils.ui_messages import UI_MESSAGES


class AgentUI:
    """Minimal, modern CLI interface for Ally."""

    def __init__(self, console: Console):
        self.console = console
        self._tool_start_time: float | None = None

    def _style(self, color_key: str) -> str:
        return THEME.get(color_key, THEME["text"])

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins}m {secs:.0f}s"

    # ─────────────────────────────────────────────────────────────
    # Branding
    # ─────────────────────────────────────────────────────────────

    def logo(self, ascii_art: str):
        """Display ASCII logo with gradient."""
        lines = ascii_art.split("\n")
        n = max(len(lines) - 1, 1)
        for i, line in enumerate(lines):
            progress = max(0.0, (i - 1) / n)
            # Gradient from soft purple to soft coral
            red = int(124 + (248 - 124) * progress)
            green = int(138 + (113 - 138) * progress)
            blue = int(255 + (113 - 255) * progress)
            color = f"#{red:02x}{green:02x}{blue:02x}"
            self.console.print(Text(line, style=f"bold {color}"))

    def help(self, model_name: str = None):
        """Display help information."""
        help_content = UI_MESSAGES["help"]["content"].copy()
        if model_name:
            help_content.append("")
            help_content.append(UI_MESSAGES["help"]["model_suffix"].format(model_name))
        help_content.append(UI_MESSAGES["help"]["footer"])

        self.console.print()
        self.console.rule("[bold]Help[/bold]", style="dim")
        self.console.print(Markdown("\n".join(help_content)))
        self.console.print()

    # ─────────────────────────────────────────────────────────────
    # Tool Execution Display
    # ─────────────────────────────────────────────────────────────

    def tool_call(self, tool_name: str, args: dict[str, Any]):
        """Display tool being executed with minimal chrome."""
        self._tool_start_time = time.time()

        self.console.print()
        self.console.print(
            f"[{self._style('dim')}]>[/{self._style('dim')}] "
            f"[bold {self._style('accent')}]{tool_name}[/bold {self._style('accent')}]"
        )

        if args:
            for k, v in args.items():
                value_str = str(v)
                # Truncate long values
                if len(value_str) > 80:
                    value_str = value_str[:77] + "..."
                elif "\n" in value_str:
                    value_str = value_str.split("\n")[0][:60] + "..."
                self.console.print(
                    f"  [{self._style('dim')}]{k}:[/{self._style('dim')}] "
                    f"[{self._style('muted')}]{value_str}[/{self._style('muted')}]"
                )

    def tool_output(self, tool_name: str, content: str):
        """Display tool completion with elapsed time."""
        elapsed = ""
        if self._tool_start_time:
            duration = time.time() - self._tool_start_time
            elapsed = f" [{self._style('dim')}]{self._format_duration(duration)}[/{self._style('dim')}]"
            self._tool_start_time = None

        # Truncate long output
        if len(content) > 800:
            content = content[:800] + "\n..."

        self.blank()
        self.console.print(
            f"  [{self._style('success')}]Done[/{self._style('success')}]{elapsed}"
        )

        # Only show output if there's meaningful content
        if content.strip() and content.strip() not in ["None", "null", ""]:
            # Show output in a subtle code block style
            for line in content.strip().split("\n")[:10]:  # Max 10 lines
                self.console.print(
                    f"    [{self._style('muted')}]{line}[/{self._style('muted')}]"
                )
            if content.strip().count("\n") > 10:
                self.console.print(
                    f"    [{self._style('dim')}]...[/{self._style('dim')}]"
                )

    # ─────────────────────────────────────────────────────────────
    # AI Response
    # ─────────────────────────────────────────────────────────────

    def ai_response(self, content: str):
        """Display AI response with minimal framing."""
        self.console.print()

        try:
            rendered = Markdown(content)
        except Exception:
            rendered = content

        panel = Panel(
            rendered,
            box=box.ROUNDED,
            border_style=self._style("border"),
            padding=(1, 2),
            title=f"[{self._style('primary')}]Ally[/{self._style('primary')}]",
            title_align="left",
        )
        self.console.print(panel)

    # ─────────────────────────────────────────────────────────────
    # Status & Messages
    # ─────────────────────────────────────────────────────────────

    def status_message(self, title: str, message: str, style: str = "primary"):
        """Display a simple inline status message."""
        prefix_map = {
            "primary": ".",
            "success": "+",
            "warning": "!",
            "error": "x",
        }
        prefix = prefix_map.get(style, ".")
        self.console.print(
            f"[{self._style(style)}]{prefix}[/{self._style(style)}] "
            f"[bold]{title}[/bold] "
            f"[{self._style('muted')}]{message}[/{self._style('muted')}]"
        )

    def info(self, message: str):
        """Display informational message."""
        self.console.print(f"[{self._style('dim')}].[/{self._style('dim')}] {message}")

    def thinking(self, message: str = "Thinking"):
        """Display a thinking/processing indicator."""
        self.console.print(
            f"[{self._style('dim')}]...[/{self._style('dim')}] [{self._style('muted')}]{message}[/{self._style('muted')}]"
        )

    def goodbye(self):
        """Display goodbye message."""
        self.console.print()
        self.console.print(
            f"[{self._style('dim')}].[/{self._style('dim')}] {UI_MESSAGES['messages']['goodbye']}"
        )
        self.console.print()

    def history_cleared(self):
        """Display history cleared confirmation."""
        self.status_message(
            "Cleared", UI_MESSAGES["messages"]["history_cleared"], "success"
        )

    def session_interrupted(self):
        """Display session interrupted message."""
        self.console.print()
        self.status_message(
            "Interrupted", UI_MESSAGES["messages"]["session_interrupted"], "warning"
        )

    def recursion_warning(self):
        """Display warning about extended processing."""
        self.console.print()
        self.console.print(
            f"[{self._style('warning')}]![/{self._style('warning')}] "
            f"[bold]Extended Session[/bold]"
        )
        self.console.print(
            f"  [{self._style('muted')}]{UI_MESSAGES['messages']['recursion_warning']}[/{self._style('muted')}]"
        )
        self.console.print()

    def warning(self, warning_msg: str):
        """Display warning message."""
        self.status_message("Warning", warning_msg, "warning")

    def error(self, error_msg: str):
        """Display error message."""
        self.status_message("Error", error_msg, "error")

    def pending_tools(self, count: int):
        """Display pending tool count."""
        self.blank()
        self.info(f"{count} tool(s) queued")

    def processing_tool(
        self, current: int, total: int, tool_name: str, tool_args: dict
    ):
        """Display tool processing progress."""
        self.console.print()
        self.console.print(
            f"[{self._style('dim')}][{current}/{total}][/{self._style('dim')}]"
        )
    
    # ─────────────────────────────────────────────────────────────
    # User Input
    # ─────────────────────────────────────────────────────────────

    def get_input(
        self,
        message: str = None,
        default: str | None = None,
        cwd: str | None = None,
        model: str | None = None,
    ) -> str:
        """Get user input with minimal prompt."""
        try:
            self.console.print()

            # Show context info on its own line
            context_parts = []
            if cwd:
                context_parts.append(cwd)
            if model:
                context_parts.append(model)

            if context_parts:
                self.console.print(
                    f"[{self._style('dim')}]{' | '.join(context_parts)}[/{self._style('dim')}]"
                )

            if message:
                self.console.print(
                    f"[{self._style('muted')}]{message}[/{self._style('muted')}]"
                )

            # Multiline key bindings
            key_binds = KeyBindings()

            @key_binds.add("c-n")
            def _(event):
                event.current_buffer.insert_text("\n")

            @key_binds.add("enter")
            def _(event):
                event.current_buffer.validate_and_handle()

            result = prompt("> ", multiline=True, key_bindings=key_binds)
            return result.strip() if result else (default or "")

        except KeyboardInterrupt:
            self.session_interrupted()
            sys.exit(0)
        except Exception as e:
            self.error(str(e))
            return default or ""

    def confirm(self, message: str, default: bool = True) -> bool:
        """Get yes/no confirmation."""
        try:
            self.console.print()
            self.console.print(
                f"[{self._style('warning')}]?[/{self._style('warning')}] {message}"
            )
            return Confirm.ask(
                ">", default=default, console=self.console, show_default=True
            )
        except KeyboardInterrupt:
            self.session_interrupted()
            sys.exit(0)
        except Exception:
            self.warning(
                f"Confirmation failed, using default: {'yes' if default else 'no'}"
            )
            return default

    def select_option(self, message: str, options: list[str]) -> int:
        """Display selection menu."""
        values = [(i, opt) for i, opt in enumerate(options)]
        try:
            self.console.print()
            result = choice(message=message, options=values)
            return result
        except KeyboardInterrupt:
            self.session_interrupted()
            sys.exit(0)
        except Exception:
            return 0

    # ─────────────────────────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────────────────────────

    def divider(self, title: str = None):
        """Print a subtle divider line."""
        if title:
            self.console.rule(
                f"[{self._style('dim')}]{title}[/{self._style('dim')}]", style="dim"
            )
        else:
            self.console.rule(style="dim")

    def blank(self):
        """Print a blank line."""
        self.console.print()


default_ui = AgentUI(Console(width=CONSOLE_WIDTH))
