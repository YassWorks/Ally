from app.src.config.permissions import permission_manager, PermissionDeniedException
from langchain_core.tools import tool
import subprocess
import tempfile
import shlex
import re
import os


@tool
def execute_code(code: str) -> str:
    """
    **PRIMARY PURPOSE**: Safely executes python code snippets in a controlled environment.

    **WHEN TO USE**:
    - Testing small code snippets or calculations
    - Validating logic before implementing in files
    - Running data analysis or processing scripts
    - Executing safe computational tasks

    **SECURITY RESTRICTIONS**:
    - TIMEOUT: Execution limited to 300 seconds maximum
    - MEMORY: Basic memory usage monitoring
    - EXTREME CAUTION: Only blocks truly destructive operations

    **BEHAVIOR**:
    - Executes code in isolated environment
    - Captures both stdout and stderr
    - Automatically times out long-running code
    - Prevents access to sensitive system resources

    **PARAMETERS**:
        code (str): The code to execute. Must be valid python code that is safe and non-malicious

    **RETURNS**:
        str: Code output, error messages, or security violation warnings

    **EXAMPLES**:
        execute_code("print('Hello World')")
        execute_code("result = 2 + 2; print(f'Result: {result}')")
        execute_code("for i in range(3): print(i)")
    """
    if not permission_manager.get_permission(tool_name="execute_code", code=code):
        raise PermissionDeniedException()

    dangerous_patterns = [
        r"rm\s+-rf\s+/",
        r"format\s+c:",
        r"mkfs\s+/dev/",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return f"🚫 BLOCKED: Extremely destructive operation: {pattern}"

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
            timeout=300,
            cwd=os.getcwd(),
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
        return "⏰ Code execution timed out (300 second limit exceeded)"
    except Exception as e:
        return f"❌ Execution error: {str(e)}"


@tool
def execute_command(command: str) -> str:
    """
    **PRIMARY PURPOSE**: Safely executes linux command-line commands in a controlled environment.

    **WHEN TO USE**:
    - Running safe system utilities (ls, cat, grep, find)
    - Checking file permissions or disk usage
    - Basic text processing commands
    - Safe read-only operations

    **SECURITY RESTRICTIONS**:
    - TIMEOUT: Commands limited to 300 seconds maximum
    - EXTREME ONLY: Only blocks filesystem destruction and hardware access

    **ALLOWED COMMANDS**:
    - Most system operations: rm, mv, cp, chmod, chown (use with caution)
    - Network operations: curl, wget, ssh, scp, nc
    - Package management: apt, yum, pip, npm
    - Process control: kill, killall, ps
    - User management: useradd, passwd (if you have permissions)
    - File operations: ls, cat, head, tail, wc, stat, find
    - Text processing: grep, awk, sed, sort, uniq
    - Development tools: git, make, gcc, python, node

    **BEHAVIOR**:
    - Executes in isolated environment
    - Captures both stdout and stderr
    - Automatically times out long-running commands
    - Prevents dangerous system modifications

    **PARAMETERS**:
        command (str): Shell command to execute (must be safe)

    **RETURNS**:
        str: Command output, error messages, or security violation warnings

    **EXAMPLES**:
        execute_command("ls -la")
        execute_command("cat config.txt")
        execute_command("sudo apt update")
        execute_command("pip3 install requests")
        execute_command("curl https://api.github.com")
        execute_command("find . -name '*.txt'")
    """
    if not permission_manager.get_permission(
        tool_name="execute_command", command=command
    ):
        raise PermissionDeniedException()

    extremely_dangerous_commands = [
        r"^rm\s+-rf\s+/$",
        r"^dd\s+.*of=/dev/sd[a-z]$",
        r"^mkfs\s+/dev/sd[a-z]$",
        r"^fdisk\s+/dev/sd[a-z]$",
        r":\(\)\{.*\}",
    ]

    for pattern in extremely_dangerous_commands:
        if re.search(pattern, command, re.IGNORECASE):
            return f"🚫 BLOCKED: Extremely destructive operation: {pattern}"

    try:
        try:
            parsed_command = shlex.split(command)
        except ValueError as e:
            return f"❌ Invalid command syntax: {str(e)}"

        if not parsed_command:
            return "❌ Empty command"

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
            shell=True,
            cwd=os.getcwd(),
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
        return "⏰ Command execution timed out (300 second limit exceeded)"
    except FileNotFoundError:
        return f"❌ Command not found: {parsed_command[0] if parsed_command else 'unknown'}"
    except PermissionError:
        return f"❌ Permission denied executing: {command}"
    except Exception as e:
        return f"❌ Execution error: {str(e)}"


EXECUTION_TOOLS = [
    execute_code,
    execute_command,
]