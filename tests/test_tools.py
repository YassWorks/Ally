import functools
import os
import tempfile

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from app.src.core.create_base_agent import SequentialToolNode
from app.src.core.permissions import permission_manager
from app.src.core.shell import run_shell
from app.src.tools import exec_tools
from app.src.tools.exec_tools import execute_code, execute_command
from app.src.tools.git_tools import diff


@pytest.fixture
def permissions(monkeypatch):
    monkeypatch.setattr(permission_manager, "always_allow", False)
    monkeypatch.setattr(permission_manager, "always_allowed_tools", set())
    monkeypatch.setattr(permission_manager.ui, "warning", lambda *a, **k: None)
    monkeypatch.setattr(permission_manager.ui.console, "print", lambda *a, **k: None)
    return monkeypatch


def test_permission_is_denied_when_the_prompt_cannot_be_shown(permissions):
    permissions.setattr(permission_manager.ui, "select_option", lambda **k: None)

    assert permission_manager.get_permission(tool_name="execute_command") is False


@pytest.mark.parametrize(
    ("choice", "allowed"), [(0, True), (1, False), (2, True), (3, True)]
)
def test_permission_choices(permissions, choice, allowed):
    permissions.setattr(permission_manager.ui, "select_option", lambda **k: choice)

    assert permission_manager.get_permission(tool_name="read_file") is allowed


def test_dangerous_commands_are_blocked_before_asking(permissions):
    def never(**kwargs):
        raise AssertionError("should not ask")

    permissions.setattr(permission_manager, "get_permission", never)

    result = execute_command.invoke({"command": "rm -rf /"})

    assert result.startswith("BLOCKED")


@pytest.fixture
def scripts_dir(permissions, tmp_path):
    permissions.setattr(permission_manager, "always_allow", True)
    permissions.setattr(
        exec_tools.tempfile,
        "NamedTemporaryFile",
        functools.partial(tempfile.NamedTemporaryFile, dir=tmp_path),
    )
    return tmp_path


def test_execute_code_runs_python_and_cleans_up(scripts_dir):
    result = execute_code.invoke({"code": "import sys; print(sys.version_info[0])"})

    assert "Output:\n3" in result
    assert os.listdir(scripts_dir) == []


def test_execute_code_timeout_reports_the_real_limit(scripts_dir, permissions):
    permissions.setattr(exec_tools, "EXEC_TIMEOUT", 1)

    result = execute_code.invoke({"code": "import time; time.sleep(10)"})

    assert result == "Code execution timed out (1 second limit exceeded)"
    assert os.listdir(scripts_dir) == []


def test_shell_keeps_quotes_and_exit_codes(tmp_path):
    assert run_shell('echo "a b"', cwd=str(tmp_path)).stdout.strip() == "a b"
    assert run_shell("exit 3", cwd=str(tmp_path)).returncode == 3


def test_git_diff_arguments_are_optional():
    schema = diff.tool_call_schema.model_json_schema()

    assert not schema.get("required")


def test_tool_errors_are_returned_to_the_model():
    @tool
    def broken(text: str) -> str:
        """Always fails."""
        raise ValueError("bad input")

    node = SequentialToolNode([broken], handle_tool_errors=True)
    call = AIMessage(
        content="", tool_calls=[{"name": "broken", "args": {"text": "x"}, "id": "1"}]
    )

    result = node({"messages": [call]})

    assert result["messages"][0].content == "Error: bad input"
