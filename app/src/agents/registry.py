from dataclasses import dataclass
from datetime import date
from pathlib import Path

from langchain_core.tools import BaseTool

from app.src.tools.exec_tools import EXECUTION_TOOLS
from app.src.tools.file_tools import FILE_TOOLS
from app.src.tools.find_tools import FIND_TOOLS
from app.src.tools.git_tools import GIT_TOOLS
from app.src.tools.web_tools import fetch_tool, search_and_scrape

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


@dataclass(frozen=True)
class AgentSpec:
    """The parts that make one kind of agent different from another.

    Attributes:
        prompt_file: Name of the built-in system prompt in ``app/prompts``.
        tools: Tools the agent always has.
    """

    prompt_file: str
    tools: tuple[BaseTool, ...] = ()


AGENT_SPECS: dict[str, AgentSpec] = {
    "general": AgentSpec(
        "general_system_prompt.md",
        (*FILE_TOOLS, *EXECUTION_TOOLS, *FIND_TOOLS, fetch_tool),
    ),
    "code_gen": AgentSpec(
        "code_gen_system_prompt.md",
        (*FILE_TOOLS, *EXECUTION_TOOLS, *FIND_TOOLS, *GIT_TOOLS),
    ),
    "brainstormer": AgentSpec("brainstormer_system_prompt.md", tuple(FILE_TOOLS)),
    "web_searcher": AgentSpec(
        "web_searcher_system_prompt.md", (search_and_scrape, fetch_tool)
    ),
}


def load_prompt(filename: str) -> str:
    """Return the contents of a prompt file from ``app/prompts``."""
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


def default_system_prompt(spec: AgentSpec) -> str:
    """Return the built-in system prompt for ``spec`` with today's date filled in."""
    today = date.today()
    return (
        load_prompt(spec.prompt_file)
        .strip()
        .replace("{date}", f"{today.day} {today:%B %Y}")
    )
