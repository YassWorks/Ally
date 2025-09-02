from app.src.agents.code_gen.config.config import get_agent
from app.src.config.ui import AgentUI
from rich.console import Console
from app.src.config.base import BaseAgent
from app.utils.constants import CONSOLE_WIDTH


class CodeGenAgent(BaseAgent):
    """Agent specialized in generating complete project structures and code.

    Creates functional codebases with proper file organization, dependencies,
    and documentation based on project requirements.

    Args:
        model_name: LLM model identifier
        api_key: API key for model provider
        system_prompt: Optional custom system prompt
        temperature: Model temperature for code consistency
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
