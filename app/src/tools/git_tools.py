import os
import subprocess

from langchain_core.tools import tool

from app.utils.logger import logger


@tool(parse_docstring=True)
def diff(
    commit1: str | None = None, commit2: str | None = None, cwd: str | None = None
) -> str:
    """Summarize which files changed and by how much, using git diff --stat.

    With no commits it shows unstaged changes. With one commit it compares that
    commit to the working tree, and with two it compares the commits.

    Args:
        commit1: Commit, branch or tag to compare from.
        commit2: Commit, branch or tag to compare to.
        cwd: Repository directory. Defaults to the working directory.
    """
    try:
        command = ["git", "diff"]
        if commit1:
            command.append(commit1)
        if commit2:
            command.append(commit2)
        command.extend(["--stat", "--ignore-space-change"])

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd(),
        )

        output = ""
        if result.stdout:
            output += f"Output:\n{result.stdout}"
        else:
            output += "No changes found."

        if result.returncode != 0:
            return f"Git error:\n{result.stderr.strip()}"

        return (
            output.strip()
            if output.strip()
            else "Command executed successfully (no output)"
        )

    except Exception as e:
        logger.error(f"Git diff execution error in {cwd}", exc_info=e)
        return f"Execution error: {str(e)}"


@tool(parse_docstring=True)
def blame(file_path: str, cwd: str | None = None) -> str:
    """Show the commit and author that last changed each line of a file.

    Args:
        file_path: File to inspect, relative to cwd.
        cwd: Repository directory. Defaults to the working directory.
    """
    try:
        command = ["git", "blame", "--line-porcelain", file_path]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd(),
        )

        if result.returncode != 0:
            return f"Git error:\n{result.stderr.strip()}"

        if not result.stdout:
            return f"No blame information found for {file_path}"

        lines = result.stdout.strip().split("\n")
        formatted_output = []
        current_commit = {}
        line_number = 1

        i = 0
        while i < len(lines):
            line = lines[i]

            if line and not line.startswith("\t"):
                parts = line.split(" ", 3)
                if len(parts) >= 3:
                    commit_hash = parts[0][:8]
                    if (
                        current_commit is None
                        or current_commit.get("hash", "") != commit_hash
                    ):
                        current_commit = {"hash": commit_hash}

                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("\t"):
                        if lines[j].startswith("author "):
                            current_commit["author"] = lines[j][7:]
                        elif lines[j].startswith("author-time "):
                            current_commit["time"] = lines[j][12:]
                        j += 1
                    i = j - 1

            elif line.startswith("\t"):
                code_content = line[1:]
                author = current_commit.get("author", "Unknown")
                commit_hash = current_commit.get("hash", "Unknown")

                formatted_output.append(
                    f"{line_number:4d} {commit_hash} ({author:15s}) {code_content}"
                )
                line_number += 1

            i += 1

        if not formatted_output:
            return f"Could not parse blame information for {file_path}"

        output = f"Blame information for {file_path}:\n\n"
        output += "\n".join(formatted_output)

        return output

    except Exception as e:
        return f"Execution error: {str(e)}"


GIT_TOOLS = [
    diff,
    blame,
]
