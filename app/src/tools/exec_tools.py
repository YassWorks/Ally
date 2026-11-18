import os
import re
import subprocess
import sys
import tempfile

from langchain_core.tools import tool

from app.src.core.permissions import PermissionDeniedException, permission_manager
from app.utils.constants import EXEC_TIMEOUT

DANGEROUS_PATTERNS = [
    r"^rm\s+-rf\s+/$",
    r"^dd\s+.*of=/dev/sd[a-z]$",
    r"^mkfs\s+/dev/sd[a-z]$",
    r"^fdisk\s+/dev/sd[a-z]$",
    r":\(\)\{.*\}",
    r"^\s*shutdown\s+-h\s+now$",
    r"^\s*reboot\s*$",
    r"^\s*init\s+0$",
    r"^\s*init\s+6$",
    r"^\s*:\s*>/dev/sd[a-z]$",
    r"^\s*dd\s+if=/dev/zero\s+of=/dev/sd[a-z]",
    r"^\s*mkfs\.\w+\s+/dev/sd[a-z]",
    r"^\s*chmod\s+777\s+/(?:\s|$)",
    r"^\s*chown\s+[^ ]+\s+/ -R",
    r"^\s*iptables\s+-F$",
    r"^\s*ufw\s+disable$",
    r"^\s*curl\s+.*\|sh$",
    r"^\s*wget\s+.*\|sh$",
    r"^\s*nc\s+-l\s+-p\s+\d+\s+-e\s+/bin/sh$",
]


def _blocked_pattern(text: str) -> str | None:
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            return pattern
    return None


def _format_result(result: subprocess.CompletedProcess, empty_message: str) -> str:
    output = ""
    if result.stdout:
        output += f"Output:\n{result.stdout}"
    if result.stderr:
        output += f"\nErrors:\n{result.stderr}"
    if result.returncode != 0:
        output += f"\nReturn code: {result.returncode}"
    return output.strip() or empty_message


@tool(parse_docstring=True)
def execute_code(code: str, cwd: str | None = None) -> str:
    """Run a Python script in a new interpreter and return its output.

    Use it to check logic, process data or automate a task. Returns stdout,
    stderr and the exit code when it is not zero.

    Args:
        code: Python source to run.
        cwd: Directory to run in. Defaults to the working directory.
    """
    if pattern := _blocked_pattern(code):
        return f"BLOCKED: Extremely destructive operation: {pattern}"

    if not permission_manager.get_permission(tool_name="execute_code", code=code):
        raise PermissionDeniedException()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(code)
        script_path = tmp_file.name

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=EXEC_TIMEOUT,
            cwd=cwd or os.getcwd(),
        )
        return _format_result(result, "Code executed successfully")
    except subprocess.TimeoutExpired:
        return f"Code execution timed out ({EXEC_TIMEOUT} second limit exceeded)"
    except Exception as e:
        return f"Execution error: {e}"
    finally:
        os.unlink(script_path)


@tool(parse_docstring=True)
def execute_command(command: str, cwd: str | None = None) -> str:
    """Run a shell command and return its output.

    Use it for builds, tests, package managers and other command line tools.
    Commands that could wreck the system, such as formatting a disk or shutting
    it down, are refused. Returns stdout, stderr and the exit code when it is
    not zero.

    Args:
        command: Command line to run.
        cwd: Directory to run in. Defaults to the working directory.
    """
    if not command.strip():
        return "Empty command"

    if pattern := _blocked_pattern(command):
        return f"BLOCKED: Extremely destructive operation: {pattern}"

    if not permission_manager.get_permission(
        tool_name="execute_command", command=command
    ):
        raise PermissionDeniedException()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=EXEC_TIMEOUT,
            shell=True,
            cwd=cwd or os.getcwd(),
        )
        return _format_result(result, "Command executed successfully (no output)")
    except subprocess.TimeoutExpired:
        return f"Command execution timed out ({EXEC_TIMEOUT} second limit exceeded)"
    except PermissionError:
        return f"Permission denied executing: {command}"
    except Exception as e:
        return f"Execution error: {e}"


EXECUTION_TOOLS = [
    execute_code,
    execute_command,
]
