from app.src.agents.general.config.config import get_agent
from app.src.core.ui import default_ui
from app.src.core.base import BaseAgent


class GeneralAgent(BaseAgent):
    """General AI agent that can do various tasks.

    Args:
        model_name: LLM model identifier
        api_key: API key for model provider
        system_prompt: Optional custom system prompt
        temperature: Model temperature for creativity control
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
