import os
from pathlib import Path

from app.src.helpers.valid_dir import validate_dir_name

_warned_env_vars: set[str] = set()


def data_root() -> Path:
    """Return the base directory for Ally's local data.

    This is ``%LOCALAPPDATA%\\Ally`` on Windows and ``~/.local/share/Ally`` elsewhere.
    """
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = (
            Path(local_app_data)
            if local_app_data
            else Path.home() / "AppData" / "Local"
        )
        return base / "Ally"
    return Path.home() / ".local" / "share" / "Ally"


def data_dir(name: str, env_var: str | None = None) -> Path:
    """Return the data directory called ``name``, creating it if needed.

    Args:
        name: Subdirectory of the data root, such as ``"history"``.
        env_var: Environment variable that overrides the location when it holds a valid path.
    """
    override = os.environ.get(env_var) if env_var else None
    if override:
        path = Path(os.path.expanduser(os.path.expandvars(override)))
        if validate_dir_name(str(path)):
            path.mkdir(parents=True, exist_ok=True)
            return path
        _warn_invalid_override(env_var)

    path = data_root() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _warn_invalid_override(env_var: str) -> None:
    if env_var in _warned_env_vars:
        return
    _warned_env_vars.add(env_var)

    from app.src.core.ui import default_ui

    default_ui.warning(
        f"Invalid directory path in ${env_var}. Using the default location."
    )
