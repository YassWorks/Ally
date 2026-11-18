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
    """Return whether ``path`` is a usable directory path on the current OS."""
    try:
        p = Path(path)
    except Exception:
        return False

    for part in p.parts:
        if part in (p.anchor, os.sep, os.altsep, os.curdir, os.pardir) or not part:
            continue

        if os.name == "nt":
            if part.upper().split(".")[0] in WINDOWS_RESERVED_NAMES:
                return False
            if any(c in WINDOWS_INVALID_CHARS for c in part):
                return False
            if part.endswith((" ", ".")):
                return False
        elif "\0" in part:
            return False

    return True
