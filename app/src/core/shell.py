import os
import shutil
import subprocess


def shell_command(command: str) -> list[str] | str:
    """Return the arguments that run ``command`` in the user's shell.

    POSIX systems use ``$SHELL``. Windows prefers PowerShell 7, then Windows PowerShell,
    then ``cmd.exe``. The command is passed as a single argument, so quotes inside it
    reach the shell unchanged.
    """
    if os.name != "nt":
        return [os.environ.get("SHELL") or "/bin/sh", "-c", command]

    for name in ("pwsh", "powershell"):
        path = shutil.which(name)
        if path:
            return [path, "-NoLogo", "-Command", command]

    return f'cmd.exe /d /s /c "{command}"'


def run_shell(command: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run ``command`` in the user's shell and capture its output."""
    return subprocess.run(
        shell_command(command),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd or os.getcwd(),
    )
