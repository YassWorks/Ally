from app.src.agents.web_searcher.web_searcher import WebSearcherAgent
from app.src.config.base import BaseAgent
from langchain_core.tools import tool


def integrate_web_search(agent: BaseAgent, web_searcher: WebSearcherAgent) -> None:
    """Enhance an agent with web search capabilities.

    Adds a search tool to the agent that delegates web research queries
    to the web searcher agent.

    Args:
        agent: Agent to enhance with search capabilities
        web_searcher: Web searcher agent to handle search queries
    """

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
            recursion_limit=100,
            quiet=True,
        )

    enhanced_graph, enhanced_agent = agent.get_agent(
        model_name=agent.model_name,
        api_key=agent.api_key,
        extra_tools=[call_searcher],
        temperature=agent.temperature,
        include_graph=True,
        provider=agent.provider,
    )

    agent.agent = enhanced_agent
    agent.graph = enhanced_graph
