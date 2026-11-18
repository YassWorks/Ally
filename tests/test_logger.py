import pytest

from app.utils.logger import logger


@pytest.mark.parametrize("level", ["debug", "info", "warning", "error", "critical"])
def test_every_level_accepts_exception_info(level):
    try:
        raise ValueError("boom")
    except ValueError as error:
        getattr(logger, level)("something failed", exc_info=error)
