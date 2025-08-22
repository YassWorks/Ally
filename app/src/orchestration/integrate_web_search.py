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
        Ask the assistant to get reliable info from the web.
        The assistant can choose the best queries for your issue to search for.
        You just need to provide a description of the problem you are facing.
        You can also provide a direct query for the assistant to use if you know it.
        Feel free to prompt it as you wish, but keep it concise.
        Args:
            query (str): The query or description of the problem to search for.
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
    )

    agent.agent = enhanced_agent
    agent.graph = enhanced_graph