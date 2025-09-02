from app.src.config.permissions import permission_manager, PermissionDeniedException
from langchain_core.tools import tool
from app.utils.constants import EXEC_TIMEOUT
import subprocess
import tempfile
import shlex
import re
import os


EXTREMEMLY_DANGEROUS_PATTERNS = [
    r"^rm\s+-rf\s+/$",  # Wipe root
    r"^dd\s+.*of=/dev/sd[a-z]$",  # Overwrite disk
    r"^mkfs\s+/dev/sd[a-z]$",  # Format disk
    r"^fdisk\s+/dev/sd[a-z]$",  # Partition disk
    r":\(\)\{.*\}",  # Fork bomb
    r"^\s*shutdown\s+-h\s+now$",  # Immediate shutdown
    r"^\s*reboot\s*$",  # Reboot system
    r"^\s*init\s+0$",  # Power off system
    r"^\s*init\s+6$",  # Reboot via init
    r"^\s*:\s*>/dev/sd[a-z]$",  # Overwrite disk with shell
    r"^\s*dd\s+if=/dev/zero\s+of=/dev/sd[a-z]",  # Zero out disk
    r"^\s*mkfs\.\w+\s+/dev/sd[a-z]",  # Filesystem creation variants
    r"^\s*chmod\s+777\s+/(?:\s|$)",  # Make root world-writable
    r"^\s*chown\s+[^ ]+\s+/ -R",  # Recursive root ownership change
    r"^\s*iptables\s+-F$",  # Flush firewall rules
    r"^\s*ufw\s+disable$",  # Disable firewall
    r"^\s*curl\s+.*\|sh$",  # Remote script execution
    r"^\s*wget\s+.*\|sh$",  # Remote script execution
    r"^\s*nc\s+-l\s+-p\s+\d+\s+-e\s+/bin/sh$",  # Netcat backdoor
]


@tool
def execute_code(code: str, cwd: str | None) -> str:
    """
    ## PRIMARY PURPOSE: 
    Execute Python code scripts in isolated temporary files.

    ## WHEN TO USE:
    - Scripting and automation tasks
    - Validate logic before implementing in files  
    - Run data analysis, processing, or computational tasks
    - Test code snippets or plot/visualize data

    ## PARAMETERS:
        code (str): Valid Python code to execute (must be safe and non-malicious)
        cwd (Optional[str]): Working directory for code execution

    ## RETURNS:
        str: Code output, error messages, or security violation warnings
    """
    if not permission_manager.get_permission(tool_name="execute_code", code=code):
        raise PermissionDeniedException()

    for pattern in EXTREMEMLY_DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return f"BLOCKED: Extremely destructive operation: {pattern}"

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name

        result = subprocess.run(
            ["python", tmp_file_path],
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
            cwd=cwd or os.getcwd(),
        )

        os.unlink(tmp_file_path)  # cleanup

        output = ""
        if result.stdout:
            output += f"Output:\n{result.stdout}"
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}"
        if result.returncode != 0:
            output += f"\nReturn code: {result.returncode}"

        return output.strip() if output.strip() else "Code executed successfully"

    except subprocess.TimeoutExpired:
        return "Code execution timed out (300 second limit exceeded)"
    except Exception as e:
        return f"Execution error: {str(e)}"


@tool
def execute_command(command: str, cwd: str | None) -> str:
    """
    ## PRIMARY PURPOSE: 
    Execute shell commands with comprehensive system access and security filtering.

    ## WHEN TO USE:
    - Run system utilities (ls, cat, grep, find)
    - File operations and text processing
    - Package management (apt, pip, npm)
    - Development tools (git, make, compilers)
    - Network operations (curl, wget, ssh)

    ## PARAMETERS:
        command (str): Shell command to execute (automatically filtered for dangerous operations)
        cwd (Optional[str]): Working directory for command execution

    ## RETURNS:
        str: Command output, error messages, or security violation warnings

    ## SECURITY:
        Blocks extremely dangerous operations (disk formatting, system shutdown, fork bombs)
    """
    if not permission_manager.get_permission(
        tool_name="execute_command", command=command
    ):
        raise PermissionDeniedException()

    for pattern in EXTREMEMLY_DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return f"BLOCKED: Extremely destructive operation: {pattern}"

    try:
        try:
            parsed_command = shlex.split(command)
        except ValueError as e:
            return f"Invalid command syntax: {str(e)}"

        if not parsed_command:
            return "Empty command"

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
            shell=True,
            cwd=cwd or os.getcwd(),
        )

        output = ""
        if result.stdout:
            output += f"Output:\n{result.stdout}"
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}"
        if result.returncode != 0:
            output += f"\nReturn code: {result.returncode}"

        return (
            output.strip()
            if output.strip()
            else "Command executed successfully (no output)"
        )

    except subprocess.TimeoutExpired:
        return "Command execution timed out (300 second limit exceeded)"
    except FileNotFoundError:
        return f"Command not found: {parsed_command[0] if parsed_command else 'unknown'}"
    except PermissionError:
        return f"Permission denied executing: {command}"
    except Exception as e:
        return f"Execution error: {str(e)}"


EXECUTION_TOOLS = [
    execute_code,
    execute_command,
]
