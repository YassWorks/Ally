import os

import pytest

from app.src.agents.registry import AGENT_SPECS
from app.src.core.permissions import permission_manager
from app.src.orchestration.integrate_web_search import integrate_web_search
from app.src.tools.file_tools import list_directory


class ToolCollector:
    def __init__(self):
        self.tools = []

    def add_tools(self, tools):
        self.tools.extend(tools)


def all_tools():
    collector = ToolCollector()
    integrate_web_search(collector, web_searcher=None)
    tools = [tool for spec in AGENT_SPECS.values() for tool in spec.tools]
    return {tool.name: tool for tool in tools + collector.tools}


TOOLS = all_tools()


@pytest.mark.parametrize("name", sorted(TOOLS))
def test_every_tool_and_argument_is_described(name):
    tool = TOOLS[name]
    properties = tool.tool_call_schema.model_json_schema()["properties"]

    assert tool.description.endswith(".")
    assert "##" not in tool.description
    assert properties
    assert all(field.get("description") for field in properties.values())


def test_list_directory_draws_a_tree_without_expanding_ignored_dirs(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(permission_manager, "always_allow", True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("", encoding="utf-8")
    (tmp_path / "node_modules" / "left-pad").mkdir(parents=True)
    (tmp_path / "README.md").write_text("", encoding="utf-8")

    result = list_directory.invoke({"path": str(tmp_path)})

    assert result.splitlines() == [
        f"{os.path.abspath(tmp_path)}/",
        "├── README.md",
        "├── node_modules/",
        "└── src/",
        "    └── app.py",
    ]
