from app.config import AgentSettings
from app.src.agents.registry import AGENT_SPECS
from app.src.core.base import BaseAgent

CODING_AGENTS = ("brainstormer", "web_searcher", "code_gen")


class AgentFactory:
    """Builds agents from their resolved settings."""

    @staticmethod
    def create_agent(agent_type: str, settings: AgentSettings) -> BaseAgent:
        """Create the agent called ``agent_type``.

        Raises:
            ValueError: If ``agent_type`` is unknown.
            RuntimeError: If the agent's model cannot be initialized.
        """
        if agent_type not in AGENT_SPECS:
            raise ValueError(f"Unknown agent type: {agent_type}")

        try:
            return BaseAgent(AGENT_SPECS[agent_type], settings)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize {agent_type} agent: {e}") from e

    @staticmethod
    def create_coding_agents(
        settings: dict[str, AgentSettings],
    ) -> dict[str, BaseAgent]:
        """Create the brainstormer, web searcher and code generation agents."""
        return {
            name: AgentFactory.create_agent(name, settings[name])
            for name in CODING_AGENTS
        }
