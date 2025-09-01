from app.src.config.permissions import permission_manager, PermissionDeniedException
from langchain_core.tools import tool
import os
import shutil


@tool
def create_wd(path: str) -> str:
    """
    ## PRIMARY PURPOSE: 
    Create a new directory at the specified path, including nested structures.

    ## WHEN TO USE:
    - Organize files into folders before file creation
    - Set up workspace directory structures
    - Create nested folder hierarchies

    ## PARAMETERS:
        path (str): Directory path to create (relative or absolute, supports nested paths)

    ## RETURNS:
        str: Success message with created path or error message
    """
    if not permission_manager.get_permission(tool_name="create_wd", path=path):
        raise PermissionDeniedException()
    try:

        os.makedirs(path, exist_ok=True)
        return f"Working directory created at {path}"
    except Exception as e:
        return f"Error creating working directory: {str(e)}"


@tool
def create_file(file_path: str, content: str) -> str:
    """
    ## PRIMARY PURPOSE: 
    Create a new file with specified text content, creating directories as needed.

    ## WHEN TO USE:
    - Generate new text files (.txt, .md, .csv, .json, .yaml, etc.)
    - Write documentation, configuration files, or data files
    - Create templates or initial file structures

    ## PARAMETERS:
        file_path (str): File path for creation (creates parent directories if needed)
        content (str): Exact text content including proper formatting, indentation, line breaks

    ## RETURNS:
        str: Success message with file path or error message
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
        return f"[ERROR] Failed to create file: {str(e)}"


@tool
def modify_file(file_path: str, old_content: str, new_content: str) -> str:
    """
    ## PRIMARY PURPOSE: 
    Replace specific text content in existing files with new content.

    ## WHEN TO USE:
    - Update configuration values or settings
    - Correct information in existing documents
    - Make targeted edits without rewriting entire files

    ## PARAMETERS:
        file_path (str): Path to existing file to modify
        old_content (str): EXACT text to replace (must match perfectly including whitespace, indentation, line breaks)
        new_content (str): Replacement text (can be different length than original)

    ## RETURNS:
        str: Success message, "Content not found" error, or other error message
    """
    if not permission_manager.get_permission(
        tool_name="modify_file",
        file_path=file_path,
        old_content=old_content,
        new_content=new_content,
    ):
        raise PermissionDeniedException()
    try:

        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read()

        if old_content not in contents:
            return f"Content not found in {file_path}"

        contents = contents.replace(old_content, new_content, 1)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(contents)
        return f"File modified at {file_path}"
    except Exception as e:
        return f"Error modifying file: {str(e)}"


@tool
def append_file(file_path: str, content: str) -> str:
    """
    ## PRIMARY PURPOSE: 
    Add new content to the end of an existing file, creating parent directories if needed.

    ## WHEN TO USE:
    - Add new entries to logs, reports, or data files
    - Extend documents with additional notes or comments
    - Append configuration settings

    ## PARAMETERS:
        file_path (str): Path to file for appending (creates parent directories if needed)
        content (str): Text to append including proper formatting, indentation, line breaks

    ## RETURNS:
        str: Success message with file path or error message
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
        return f"Error appending file: {str(e)}"


@tool
def delete_file(file_path: str) -> str:
    """
    ## PRIMARY PURPOSE: 
    Permanently remove a file from the filesystem.

    ## WHEN TO USE:
    - Clean up temporary or unnecessary files
    - Remove outdated documents or cached data
    - Delete files created by mistake

    ## PARAMETERS:
        file_path (str): Path to file to delete

    ## RETURNS:
        str: Success message with deleted path or error message
    """
    if not permission_manager.get_permission(
        tool_name="delete_file", file_path=file_path
    ):
        raise PermissionDeniedException()
    try:

        os.remove(file_path)
        return f"File deleted at {file_path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"


@tool
def delete_directory(path: str) -> str:
    """
    ## PRIMARY PURPOSE: 
    Permanently remove a directory and all its contents recursively.

    ## WHEN TO USE:
    - Clean up entire folders no longer needed
    - Remove temporary directories after processing
    - Delete old project or cache directories

    ## PARAMETERS:
        path (str): Path to directory to delete (all contents will be removed)

    ## RETURNS:
        str: Success message with deleted path or error message
    """
    if not permission_manager.get_permission(tool_name="delete_directory", path=path):
        raise PermissionDeniedException()
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            return f"Directory deleted at {path}"
        else:
            return f"Directory does not exist: {path}"
    except Exception as e:
        return f"Error deleting directory: {str(e)}"


@tool
def read_file(file_path: str) -> str:
    """
    ## PRIMARY PURPOSE: 
    Read and return the complete text content of any file.

    ## WHEN TO USE:
    - Examine existing files before making changes
    - Review configuration files, documents, or code
    - Understand file structure and content for modifications

    ## PARAMETERS:
        file_path (str): Path to file to read

    ## RETURNS:
        str: Complete file contents or error message if read fails
    """
    if not permission_manager.get_permission(
        tool_name="read_file", file_path=file_path
    ):
        raise PermissionDeniedException()
    try:

        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read()
        return contents
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def list_directory(path: str = ".") -> str:
    """
    ## PRIMARY PURPOSE: 
    Display complete directory structure in professional ASCII tree format.

    ## WHEN TO USE:
    - Explore unknown directory structures  
    - Understand file organization before making changes
    - Find specific file types or locations
    - Get overview of nested folder contents

    ## PARAMETERS:
        path (str): Directory to explore (defaults to current directory)

    ## RETURNS:
        str: Professional ASCII tree showing all files and directories with full hierarchy
    """
    if not permission_manager.get_permission(tool_name="list_directory", path=path):
        raise PermissionDeniedException()

    def _list_directory_recursive(
        current_path: str,
        current_depth: int = 0,
        is_last: bool = True,
        parent_prefix: str = "",
    ) -> list:
        """Helper function to recursively build directory tree"""
        items = []

        try:
            all_items = os.listdir(current_path)
            dirs = []
            files = []

            for item in all_items:
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    files.append(item)

            # Sort files and directories
            all_sorted = sorted(files) + sorted(dirs)
            total_items = len(all_sorted)

            for i, item_name in enumerate(all_sorted):
                is_last_item = i == total_items - 1
                item_path = os.path.join(current_path, item_name)

                # Determine the prefix for this item
                if current_depth == 0:
                    prefix = ""
                else:
                    if is_last_item:
                        prefix = parent_prefix + "└── "
                    else:
                        prefix = parent_prefix + "├── "

                # Add the item
                if os.path.isdir(item_path):
                    items.append(f"{prefix}{item_name}/")

                    # Recursively process subdirectory
                    if current_depth == 0:
                        new_parent_prefix = "│   "
                    else:
                        if is_last_item:
                            new_parent_prefix = parent_prefix + "    "
                        else:
                            new_parent_prefix = parent_prefix + "│   "

                    sub_items = _list_directory_recursive(
                        item_path, current_depth + 1, is_last_item, new_parent_prefix
                    )
                    items.extend(sub_items)

                    # Add empty line after directory contents if not the last item
                    if not is_last_item and sub_items:
                        items.append(parent_prefix + "│")
                else:
                    items.append(f"{prefix}{item_name}")

        except PermissionError:
            if current_depth == 0:
                items.append("❌ Permission denied")
            else:
                items.append(f"{parent_prefix}❌ Permission denied")
        except Exception as e:
            if current_depth == 0:
                items.append(f"❌ Error: {str(e)}")
            else:
                items.append(f"{parent_prefix}❌ Error: {str(e)}")

        return items

    try:
        result = [f"{os.path.abspath(path)}/", "│"]

        items = _list_directory_recursive(path)
        result.extend(items)

        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


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
