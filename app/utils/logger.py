import logging
from datetime import datetime

from app.utils.paths import data_dir


class AllyLogger:
    """Centralized logging system for Ally."""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize the logger with file and console handlers."""
        log_path = data_dir("logs") / f"ally_{datetime.now().strftime('%Y%m%d')}.log"

        # Create logger
        self._logger = logging.getLogger("ally")
        self._logger.setLevel(logging.DEBUG)
        # Prevent logging from propagating to root logger (which outputs to console)
        self._logger.propagate = False

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

            self._logger.addHandler(file_handler)

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
