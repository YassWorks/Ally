import os

import pytest

from app.src.helpers.valid_dir import validate_dir_name


def test_accepts_regular_paths(tmp_path):
    assert validate_dir_name(str(tmp_path))
    assert validate_dir_name("projects/ally")


@pytest.mark.skipif(os.name != "nt", reason="Windows naming rules")
@pytest.mark.parametrize("path", [r"C:\work\CON", r"C:\work\a|b", r"C:\work\trailing."])
def test_rejects_invalid_windows_names(path):
    assert not validate_dir_name(path)


@pytest.mark.skipif(os.name == "nt", reason="POSIX naming rules")
def test_rejects_null_byte_on_posix():
    assert not validate_dir_name("/tmp/bad\0name")
