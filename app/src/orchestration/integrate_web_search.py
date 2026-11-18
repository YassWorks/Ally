from langchain_core.tools import tool

from app.src.core.base import BaseAgent
from app.utils.constants import RECURSION_LIMIT


def integrate_web_search(agent: BaseAgent, web_searcher: BaseAgent) -> None:
    """Give ``agent`` a tool that hands research questions to ``web_searcher``."""

    @tool(parse_docstring=True)
    def call_searcher(query: str) -> str:
        """Ask the web research agent to answer a question from current sources.

        Use it for recent facts, documentation and anything you are not sure
        about. The agent searches the web, reads the pages it finds and returns
        a summary.

        Args:
            query: Question or topic to research, with enough context to search
                for it.
        """
        return web_searcher.invoke(
            message=query,
            recursion_limit=RECURSION_LIMIT,
            quiet=True,
        )

    agent.add_tools([call_searcher])
