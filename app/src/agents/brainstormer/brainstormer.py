from app.src.agents.brainstormer.config.config import get_agent
from app.src.config.ui import AgentUI
from rich.console import Console
from app.src.config.base import BaseAgent
from app.utils.constants import CONSOLE_WIDTH


class BrainstormerAgent(BaseAgent):
    """Agent specialized in analyzing project descriptions and extracting ideas.

    Processes user input to identify core concepts, technical requirements,
    and feature suggestions for project development.

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

        console = Console(width=CONSOLE_WIDTH)
        ui = AgentUI(console)

        super().__init__(
            model_name=model_name,
            api_key=api_key,
            system_prompt=system_prompt,
            agent=agent,
            console=console,
            ui=ui,
            get_agent=get_agent,
            temperature=temperature,
            graph=graph,
            provider=provider,
        )
