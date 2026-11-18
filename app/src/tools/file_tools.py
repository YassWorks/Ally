import os
import shutil

from langchain_core.tools import tool

from app.src.core.permissions import PermissionDeniedException, permission_manager
from app.src.tools.find_tools import IGNORED_DIRS
from app.utils.logger import logger


@tool(parse_docstring=True)
def create_wd(path: str) -> str:
    """Create a directory, including any missing parent directories.

    Args:
        path: Directory to create, absolute or relative to the working directory.
    """
    if not permission_manager.get_permission(tool_name="create_wd", path=path):
        raise PermissionDeniedException()
    try:
        os.makedirs(path, exist_ok=True)
        return f"Working directory created at {path}"
    except Exception as e:
        logger.error(f"Failed to create working directory: {path}", exc_info=e)
        return f"Error creating working directory: {e}"


@tool(parse_docstring=True)
def create_file(file_path: str, content: str) -> str:
    """Write a file with the given content, replacing it if it already exists.

    Missing parent directories are created.

    Args:
        file_path: Path of the file to write.
        content: Full text of the file, with its exact indentation and line breaks.
    """
    if not permission_manager.get_permission(
        tool_name="create_file", file_path=file_path, content=content
    ):
        raise PermissionDeniedException()
    try:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created at {file_path}"
    except Exception as e:
        logger.error(f"Failed to create file: {file_path}", exc_info=e)
        return f"Error creating file: {e}"


@tool(parse_docstring=True)
def modify_file(file_path: str, old_content: str, new_content: str) -> str:
    """Replace the first occurrence of a block of text in an existing file.

    Read the file first: old_content must match it exactly, including whitespace
    and line breaks.

    Args:
        file_path: Path of the file to edit.
        old_content: Exact text to replace.
        new_content: Text to put in its place.
    """
    if not permission_manager.get_permission(
        tool_name="modify_file",
        file_path=file_path,
        old_content=old_content,
        new_content=new_content,
    ):
        raise PermissionDeniedException()
    try:
        with open(file_path, encoding="utf-8") as f:
            contents = f.read()

        if old_content not in contents:
            return f"Content not found in {file_path}"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(contents.replace(old_content, new_content, 1))
        return f"File modified at {file_path}"
    except Exception as e:
        logger.error(f"Failed to modify file: {file_path}", exc_info=e)
        return f"Error modifying file: {e}"


@tool(parse_docstring=True)
def append_file(file_path: str, content: str) -> str:
    """Add text to the end of a file, creating the file if it does not exist.

    Args:
        file_path: Path of the file to extend.
        content: Text to add, including any leading line break it needs.
    """
    if not permission_manager.get_permission(
        tool_name="append_file",
        file_path=file_path,
        content=content,
    ):
        raise PermissionDeniedException()
    try:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Content appended to {file_path}"
    except Exception as e:
        logger.error(f"Failed to append to file: {file_path}", exc_info=e)
        return f"Error appending file: {e}"


@tool(parse_docstring=True)
def delete_file(file_path: str) -> str:
    """Delete a file.

    Args:
        file_path: Path of the file to delete.
    """
    if not permission_manager.get_permission(
        tool_name="delete_file", file_path=file_path
    ):
        raise PermissionDeniedException()
    try:
        os.remove(file_path)
        return f"File deleted at {file_path}"
    except Exception as e:
        logger.error(f"Failed to delete file: {file_path}", exc_info=e)
        return f"Error deleting file: {e}"


@tool(parse_docstring=True)
def delete_directory(path: str) -> str:
    """Delete a directory and everything inside it.

    Args:
        path: Directory to delete.
    """
    if not permission_manager.get_permission(tool_name="delete_directory", path=path):
        raise PermissionDeniedException()
    try:
        if not os.path.exists(path):
            return f"Directory does not exist: {path}"
        shutil.rmtree(path)
        return f"Directory deleted at {path}"
    except Exception as e:
        logger.error(f"Failed to delete directory: {path}", exc_info=e)
        return f"Error deleting directory: {e}"


@tool(parse_docstring=True)
def read_file(file_path: str) -> str:
    """Return the full text of a file.

    Args:
        file_path: Path of the file to read.
    """
    if not permission_manager.get_permission(
        tool_name="read_file", file_path=file_path
    ):
        raise PermissionDeniedException()
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file: {file_path}", exc_info=e)
        return f"Error reading file: {e}"


@tool(parse_docstring=True)
def list_directory(path: str = ".") -> str:
    """Show the files and folders under a directory as a tree.

    Folders such as .git, node_modules and virtual environments are shown but not
    expanded.

    Args:
        path: Directory to list. Defaults to the working directory.
    """
    if not permission_manager.get_permission(tool_name="list_directory", path=path):
        raise PermissionDeniedException()
    if not os.path.isdir(path):
        return f"Not a directory: {path}"
    return "\n".join([f"{os.path.abspath(path)}/", *_tree(path)])


def _tree(path: str, prefix: str = "") -> list[str]:
    try:
        entries = sorted(os.scandir(path), key=lambda e: (e.is_dir(), e.name))
    except OSError as e:
        logger.warning(f"Cannot list directory: {path}", exc_info=e)
        return [f"{prefix}└── (cannot list: {e.strerror or e})"]

    lines = []
    for index, entry in enumerate(entries):
        last = index == len(entries) - 1
        branch, indent = ("└── ", "    ") if last else ("├── ", "│   ")
        if not entry.is_dir():
            lines.append(f"{prefix}{branch}{entry.name}")
            continue
        lines.append(f"{prefix}{branch}{entry.name}/")
        if entry.name not in IGNORED_DIRS:
            lines.extend(_tree(entry.path, prefix + indent))
    return lines


FILE_TOOLS = [
    create_wd,
    create_file,
    modify_file,
    append_file,
    delete_file,
    delete_directory,
    read_file,
    list_directory,
]
