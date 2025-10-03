from app.src.agents.web_searcher.config.config import get_agent
from app.src.core.ui import default_ui
from app.src.core.base import BaseAgent


class WebSearcherAgent(BaseAgent):
    """Agent specialized in web research and information gathering.

    Searches for relevant information and best practices to enhance
    project generation with up-to-date knowledge.

    Args:
        model_name: LLM model identifier
        api_key: API key for model provider
        system_prompt: Optional custom system prompt
        temperature: Model temperature for search query diversity
    """

    def __init__(
        self,
        model_name: str,
        api_key: str,
        system_prompt: str = None,
        temperature: float = 0,
        provider: str = None,
    ):
        graph, agent = get_agent(
            model_name=model_name,
            api_key=api_key,
            system_prompt=system_prompt,
            temperature=temperature,
            include_graph=True,
            provider=provider,
        )

        super().__init__(
            model_name=model_name,
            api_key=api_key,
            system_prompt=system_prompt,
            agent=agent,
            ui=default_ui,
            get_agent=get_agent,
            temperature=temperature,
            graph=graph,
            provider=provider,
        )
