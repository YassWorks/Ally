import logging
import os
from datetime import datetime
from pathlib import Path
from app.utils.constants import DEFAULT_PATHS


class AllyLogger:
    """Centralized logging system for Ally."""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AllyLogger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize the logger with file and console handlers."""
        # Expand environment variables and user home directory
        log_dir = os.path.expandvars(DEFAULT_PATHS["logs"])
        log_dir = os.path.expanduser(log_dir)

        # Create log directory if it doesn't exist
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        # Create log filename with timestamp
        log_filename = f"ally_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = os.path.join(log_dir, log_filename)

        # Create logger
        self._logger = logging.getLogger("ally")
        self._logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers if logger already configured
        if not self._logger.handlers:
            # File handler - logs everything
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)

            # Console handler - only warnings and above (optional, can be removed if not needed)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_formatter = logging.Formatter("%(levelname)s: %(message)s")
            console_handler.setFormatter(console_formatter)

            self._logger.addHandler(file_handler)
            # Uncomment the next line if you want console logging for warnings/errors
            # self._logger.addHandler(console_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._logger.warning(message, extra=kwargs)

    def error(self, message: str, exc_info=None, **kwargs):
        """Log error message with optional exception info."""
        self._logger.error(message, exc_info=exc_info, extra=kwargs)

    def critical(self, message: str, exc_info=None, **kwargs):
        """Log critical message with optional exception info."""
        self._logger.critical(message, exc_info=exc_info, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self._logger.exception(message, extra=kwargs)


# Create singleton instance
logger = AllyLogger()
