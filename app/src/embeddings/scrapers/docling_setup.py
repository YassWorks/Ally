from app.src.core.ui import default_ui
from app.utils.constants import DEFAULT_PATHS
from app.src.helpers.valid_dir import validate_dir_name
from pathlib import Path
import os


# configure parsing models path
ARTIFACTS_PATH = ""
if "ALLY_PARSING_MODELS_DIR" in os.environ:
    ARTIFACTS_PATH = Path(os.getenv("ALLY_PARSING_MODELS_DIR"))
    if not validate_dir_name(str(ARTIFACTS_PATH)):
        ARTIFACTS_PATH = ""
        default_ui.warning(
            "Invalid directory path found in $ALLY_PARSING_MODELS_DIR. Reverting to default path."
        )

if not ARTIFACTS_PATH:
    ARTIFACTS_PATH = DEFAULT_PATHS["parsing_models"]
    if os.name == "nt":
        ARTIFACTS_PATH = Path(os.path.expandvars(ARTIFACTS_PATH))
    else:
        ARTIFACTS_PATH = Path(os.path.expanduser(ARTIFACTS_PATH))


def setup(path: str = ARTIFACTS_PATH) -> None:
    """
    Prepare environment and download Docling parsing models.

    Ensures required packages are installed and downloads parsing artifacts
    (parsing models, EasyOCR model, and smolvlm).

    Parameters
    - path (str | Path): target directory for model files (defaults to ARTIFACTS_PATH).

    Notes
    - OpenGL drivers may be required for some Docling components.
    - Installs the `docling` package (uses CPU PyTorch wheel by default).
    - Raises an exception on failure.
    """

    with default_ui.console.status(
        "Docling setup found. Installing additional required packages: Docling"
    ):
        import subprocess
        import sys

        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--extra-index-url",
                "https://download.pytorch.org/whl/cpu",  # CPU-only PyTorch. Adjust if needed.
                "docling==2.55.1",  # TODO: fix
                "-qqq",
            ]
        )

    try:
        os.makedirs(path, exist_ok=True)
        with default_ui.console.status("Downloading parsing models..."):
            from docling.utils.model_downloader import download_models

            download_models(
                output_dir=path,
                progress=False,
                with_smolvlm=True,
            )

    except Exception as e:
        default_ui.error(f"Failed to download parsing models: {e}")
        raise
