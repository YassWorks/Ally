from app.src.core import create_base_agent
from app.utils.paths import data_dir


def test_env_override(tmp_path, monkeypatch):
    target = tmp_path / "custom"
    monkeypatch.setenv("ALLY_TEST_DIR", str(target))

    assert data_dir("history", "ALLY_TEST_DIR") == target
    assert target.is_dir()


def test_default_location(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    path = data_dir("history")

    assert path.is_dir()
    assert path.name == "history"
    assert path.parent.name == "Ally"


def test_checkpointer_is_shared(tmp_path, monkeypatch):
    monkeypatch.setenv("ALLY_HISTORY_DIR", str(tmp_path))
    monkeypatch.setattr(create_base_agent, "_checkpointer", None)

    first = create_base_agent.get_checkpointer()

    assert create_base_agent.get_checkpointer() is first
    assert (tmp_path / "history.sqlite").exists()
