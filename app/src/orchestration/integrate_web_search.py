from langchain_core.tools import tool

from app.src.core.base import BaseAgent
from app.utils.constants import RECURSION_LIMIT


def integrate_web_search(agent: BaseAgent, web_searcher: BaseAgent) -> None:
    """Give ``agent`` a tool that hands research questions to ``web_searcher``."""

    @tool
    def call_searcher(query: str) -> str:
        """
        ## PRIMARY PURPOSE:
        Delegate web research queries to specialized web search agent for reliable information.

        ## WHEN TO USE:
        - Research technical topics, implementation details, or best practices
        - Find current information about tools, frameworks, or approaches
        - Gather multiple perspectives on development solutions

        ## PARAMETERS:
            query (str): Query description or specific search terms for web research

        ## RETURNS:
            str: Comprehensive research results from web search agent
        """
        return web_searcher.invoke(
            message=query,
            recursion_limit=RECURSION_LIMIT,
            quiet=True,
        )

    agent.add_tools([call_searcher])
