from app.src.config.permissions import permission_manager, PermissionDeniedException
from langchain_core.tools import tool
import os
import shutil


@tool
def create_wd(path: str) -> str:
    """
    **PRIMARY PURPOSE**: Creates a new directory/folder at the specified path.

    **WHEN TO USE**:
    - When you need to organize files into structured folders
    - Before placing files in a location that doesn't exist yet
    - Setting up workspace directories for different types of content
    - Creating nested folder structures in one operation

    **BEHAVIOR**:
    - Creates the directory and ALL parent directories if they don't exist
    - Will NOT fail if the directory already exists (safe to use repeatedly)
    - Similar to running "mkdir -p" in terminal

    **PARAMETERS**:
        path (str): The directory path to create. Can be:
                   - Relative: "documents", "media/images", "archive/2024"
                   - Absolute: "/home/user/workspace", "/opt/data/projects"
                   - Nested: "deep/nested/folder/structure"

    **RETURNS**:
        str: Success message with created path, or error message if failed

    **EXAMPLES**:
        create_wd("new_folder")               # Creates folder in current directory
        create_wd("documents/reports")        # Creates nested structure
        create_wd("/home/user/workspace")     # Creates with absolute path
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
    **PRIMARY PURPOSE**: Creates a brand new file with specified content.

    **WHEN TO USE**:
    - Creating new text files (.txt, .md, .csv, etc.)
    - Generating configuration files (.json, .yaml, .ini, etc.)
    - Writing documentation or notes
    - Creating data files or templates
    - Establishing any type of text-based file

    **BEHAVIOR**:
    - Creates ALL necessary parent directories automatically
    - OVERWRITES existing files without warning
    - Writes content exactly as provided (preserves formatting)

    **PARAMETERS**:
        file_path (str): Where to create the file. Examples:
                        - "notes.txt" (current directory)
                        - "documents/report.md" (creates documents/ if needed)
                        - "/home/user/config.json"
        content (str): Exact text content for the file. Include proper:
                      - Indentation and whitespace
                      - Line breaks (\n)
                      - Any formatting needed

    **RETURNS**:
        str: Success message with file path, or error message if failed

    **WARNING**: This OVERWRITES existing files! Use modify_file() for edits.

    **EXAMPLES**:
        create_file("notes.txt", "Meeting notes from today")
        create_file("config/settings.json", '{"theme": "dark"}')
        create_file("README.md", "# My Project\n\nDescription here")
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
    **PRIMARY PURPOSE**: Updates existing files by replacing specific content.

    **WHEN TO USE**:
    - Correcting information in existing files
    - Updating configuration values or settings
    - Changing specific text sections
    - Making targeted edits without rewriting entire files
    - Updating data or content in documents

    **BEHAVIOR**:
    - Finds EXACT match of old_content and replaces with new_content
    - Only replaces the FIRST occurrence found
    - File must already exist (use create_file() for new files)
    - Preserves all other file content unchanged

    **PARAMETERS**:
        file_path (str): Path to existing file to modify
        old_content (str): EXACT text to replace (must match perfectly including:
                          - All whitespace and indentation
                          - Line breaks and spacing
                          - Capitalization and punctuation)
        new_content (str): Replacement text (can be longer/shorter than original)

    **RETURNS**:
        str: Success message, "Content not found" error, or other error message

    **CRITICAL**: old_content must match EXACTLY or replacement will fail!

    **EXAMPLES**:
        modify_file("notes.txt", "Meeting at 2pm", "Meeting at 3pm")
        modify_file("config.json", '"theme": "light"', '"theme": "dark"')
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
    **PRIMARY PURPOSE**: Appends new content to the end of an existing file.

    **WHEN TO USE**:
    - Adding new data to logs or reports
    - Appending notes or comments to documents
    - Extending configuration files with additional settings
    - Adding new entries to data files

    **BEHAVIOR**:
    - Appends content exactly as provided (preserves formatting)
    - Creates the file if it doesn't exist (like "touch" command)
    - Does NOT modify existing content, only adds to the end

    **PARAMETERS**:
        file_path (str): Path to file to append. Examples:
                        - "log.txt" (current directory)
                        - "data/records.csv" (creates data/ if needed)
                        - "/home/user/notes.txt"
        content (str): Text to append. Include proper:
                      - Indentation and whitespace
                      - Line breaks (\n)
                      - Any formatting needed

    **RETURNS**:
        str: Success message with file path, or error message if failed

    **EXAMPLES**:
        append_file("log.txt", "New log entry at 3pm")
        append_file("data/records.csv", "id,name\n1,John Doe")
        append_file("notes.txt", "\n# Additional Notes\nContent here")
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
    **PRIMARY PURPOSE**: Permanently removes a file from the filesystem.

    **WHEN TO USE**:
    - Cleaning up temporary or unnecessary files
    - Removing outdated documents
    - Deleting log files or cached data
    - Removing files created by mistake
    - Cleaning up before reorganizing files

    **BEHAVIOR**:
    - PERMANENTLY deletes the file (cannot be undone)
    - Only works on files, not directories
    - Will fail if file doesn't exist

    **PARAMETERS**:
        file_path (str): Path to file to delete. Examples:
                        - "temp.txt"
                        - "documents/old_report.pdf"
                        - "/var/log/debug.log"

    **RETURNS**:
        str: Success message with deleted path, or error message if failed

    **DANGER**: This operation is PERMANENT and IRREVERSIBLE!

    **SAFETY TIPS**:
    - Double-check file path before deletion
    - Consider backing up important files first
    - This tool only deletes FILES, not directories

    **EXAMPLES**:
        delete_file("temp.log")              # Remove temporary file
        delete_file("old_document.txt")      # Remove outdated file
        delete_file("/tmp/session.tmp")      # Clean cache file
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
    **PRIMARY PURPOSE**: Permanently removes a directory and all its contents.

    **WHEN TO USE**:
    - Cleaning up entire folders that are no longer needed
    - Removing temporary directories created during processing
    - Deleting old project directories
    - Clearing out cache or log directories

    **BEHAVIOR**:
    - Deletes the directory and ALL files/subdirectories inside it
    - PERMANENTLY removes everything (cannot be undone)
    - Will fail if directory doesn't exist or is not empty

    **PARAMETERS**:
        path (str): Path to directory to delete. Examples:
                   - "temp_folder"
                   - "projects/old_project"
                   - "/var/logs/old_logs"

    **RETURNS**:
        str: Success message with deleted path, or error message if failed

    **DANGER**: This operation is PERMANENT and IRREVERSIBLE!

    **SAFETY TIPS**:
    - Double-check directory path before deletion
    - Consider backing up important data first
    - This tool only deletes DIRECTORIES, not individual files

    **EXAMPLES**:
        delete_directory("temp_folder")              # Remove temporary folder
        delete_directory("projects/old_project")     # Remove old project folder
        delete_directory("/var/logs/old_logs")       # Clean up log directory
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
    **PRIMARY PURPOSE**: Reads and returns the complete content of any text file.

    **WHEN TO USE**:
    - Examining existing files before making changes
    - Reading configuration files to understand settings
    - Reviewing documents or notes
    - Checking file contents to determine what modifications are needed
    - Understanding file structure and existing content

    **BEHAVIOR**:
    - Returns the ENTIRE file content as a single string
    - Preserves all formatting, indentation, and line breaks
    - Works with any text-based file format
    - Will fail if file doesn't exist or isn't readable

    **PARAMETERS**:
        file_path (str): Path to file to read. Examples:
                        - "notes.txt" (current directory)
                        - "config/settings.json"
                        - "documents/README.md"
                        - "/etc/config/file.txt"

    **RETURNS**:
        str: Complete file contents, or error message if file cannot be read

    **USE BEFORE**: Making changes to understand current file state

    **EXAMPLES**:
        read_file("settings.json")           # Check configuration
        read_file("documents/notes.txt")     # Review document content
        read_file("/var/data/report.csv")    # Read data file
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
    **PRIMARY PURPOSE**: Shows all files and folders in a professional ASCII tree structure.

    **WHEN TO USE**:
    - Exploring an unknown directory structure
    - Understanding how files are organized before making changes
    - Finding where specific types of files are located
    - Getting an overview of a directory's contents
    - Discovering what files exist in nested folders

    **BEHAVIOR**:
    - Recursively explores all subdirectories
    - Shows hierarchical structure with ASCII tree characters (├── └── │)
    - Directories are marked with trailing "/"
    - Files and directories are sorted alphabetically within each level
    - Displays absolute path as header

    **OUTPUT FORMAT**:
        /absolute/path/to/directory/
        │
        ├── file1.txt
        ├── file2.py
        ├── subdirectory/
        │   ├── nested_file.md
        │   └── another_file.json
        └── last_file.txt

    **PARAMETERS**:
        path (str): Directory to explore. Defaults to current directory (".")
                   Examples: ".", "documents", "/home/user/projects"

    **RETURNS**:
        str: Professional ASCII tree view of all files and directories

    **USEFUL FOR**: Getting bearings in unfamiliar directory structures

    **EXAMPLES**:
        list_directory(".")                      # Show current directory structure
        list_directory("documents")              # Explore documents/
        list_directory("/var/log")               # Show system log directory contents
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
