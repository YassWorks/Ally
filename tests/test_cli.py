import argparse
import os

import pytest
from langchain_core.messages import AIMessage

from app.config import AGENT_TYPES, AllyConfig
from app.src.cli.cli import CLI
from app.src.core.permissions import permission_manager
from app.src.core.ui import default_ui
from app.src.helpers.valid_dir import validate_dir_name


@pytest.fixture
def cli(fake_llm, settings, monkeypatch):
    monkeypatch.setattr(permission_manager, "always_allow", False)
    for name in ("logo", "welcome", "goodbye", "ai_response"):
        monkeypatch.setattr(default_ui, name, lambda *a, **k: None)
    return CLI(AllyConfig(agents=dict.fromkeys(AGENT_TYPES, settings)), stream=False)


def chat_args(directory, prompt):
    return argparse.Namespace(
        d=str(directory),
        p=prompt,
        i=None,
        allow_all_tools=True,
        create_project=False,
    )


@pytest.mark.parametrize("path", [".", "..", "../sibling", "./nested/dir"])
def test_relative_directories_are_valid(path):
    assert validate_dir_name(path)


def test_session_works_inside_the_chosen_directory(
    cli, fake_llm, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    workdir = tmp_path / "projects" / "demo"
    fake_llm.replies.extend(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "create_file",
                        "args": {"file_path": "notes.txt", "content": "hello"},
                        "id": "call_1",
                    }
                ],
            ),
            "Created it.",
        ]
    )
    monkeypatch.setattr(default_ui, "get_input", lambda *a, **k: "/q")

    cli.start_chat(chat_args(workdir, "create notes.txt"))

    assert (workdir / "notes.txt").read_text(encoding="utf-8") == "hello"
    assert not (tmp_path / "notes.txt").exists()
    assert os.getcwd() == str(tmp_path)
