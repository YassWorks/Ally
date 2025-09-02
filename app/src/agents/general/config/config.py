from app.src.config.create_base_agent import create_base_agent
from app.src.agents.general.config.tools import ALL_TOOLS
import os


def get_agent(
    model_name: str,
    api_key: str,
    system_prompt: str = None,
    extra_tools: list = None,
    temperature: float = 0,
    include_graph: bool = True,
    provider: str = None,
):
    """Create a general agent.
    
    Args:
        model_name: LLM model identifier
        api_key: API key for model provider
        system_prompt: Optional custom system prompt
        extra_tools: Additional tools to include
        temperature: Model temperature for creativity
        include_graph: Whether to return the graph along with agent
        
    Returns:
        Agent instance or tuple of (graph, agent) if include_graph is True
    """
    tools = ALL_TOOLS.copy()
    if extra_tools:
        tools.extend(extra_tools)

    if system_prompt is None or system_prompt.strip() == "":
        dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(dir, "system_prompt.txt"), "r") as file:
            system_prompt = file.read().strip()

    return create_base_agent(
        model_name=model_name,
        api_key=api_key,
        tools=tools,
        system_prompt=system_prompt,
        temperature=temperature,
        include_graph=include_graph,
        provider=provider,
    )
