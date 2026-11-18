import logging
import os
import sys
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Run the ``ally`` command."""
    from app.src.cli.flags import ArgsParser
    from app.src.core.ui import default_ui

    args = ArgsParser.get_args(ui=default_ui, user_args=sys.argv[1:])

    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
    _silence_library_logs()

    from app.config import ConfigError, load_config
    from app.utils.logger import logger
    from app.utils.ui_messages import UI_MESSAGES

    try:
        config = load_config(config_path())
    except ConfigError as e:
        logger.error(str(e))
        default_ui.error(str(e))
        sys.exit(1)

    try:
        with default_ui.console.status("Starting Ally..."):
            from app.src.cli.cli import CLI

            cli = CLI(config)
    except Exception as e:
        logger.exception("Failed to start Ally")
        default_ui.error(
            f"{UI_MESSAGES['errors']['failed_initialize_agents']}\n{type(e).__name__}: {e}"
        )
        sys.exit(1)

    cli.start_chat(args)


def config_path() -> Path:
    """Return the config file to use: ``$ALLY_CONFIG`` if set, else ``config.json``."""
    override = os.environ.get("ALLY_CONFIG")
    return Path(override).expanduser() if override else PROJECT_ROOT / "config.json"


def _silence_library_logs() -> None:
    logging.basicConfig(level=logging.CRITICAL)
    for module in ("torch", "huggingface_hub", "onnxruntime"):
        warnings.filterwarnings("ignore", category=Warning, module=module)


if __name__ == "__main__":
    main()
