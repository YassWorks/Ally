import os
from pathlib import Path


WINDOWS_INVALID_CHARS = '<>:"/\\|?*'
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def validate_dir_name(path: str) -> bool:
    """
    Validate a directory path for the current OS.
    Returns True if the path is safe to use.
    """
    try:
        p = Path(path)
    except Exception:
        return False

    for part in p.parts:

        if part in (p.anchor, os.sep, os.altsep) or not part:
            continue

        # Windows-specific checks
        if os.name == "nt":

            if part.upper().split(".")[0] in WINDOWS_RESERVED_NAMES:
                return False

            if any(c in WINDOWS_INVALID_CHARS for c in part):
                return False

            if part.endswith(" ") or part.endswith("."):
                return False

        # POSIX-specific checks
        else:
            if "\0" in part:
                return False

    return True
