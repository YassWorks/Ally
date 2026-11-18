from app.config import AgentSettings
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
        from app.src.agents.brainstormer.brainstormer import BrainstormerAgent
        from app.src.agents.code_gen.code_gen import CodeGenAgent
        from app.src.agents.general.general import GeneralAgent
        from app.src.agents.web_searcher.web_searcher import WebSearcherAgent

        agent_classes = {
            "brainstormer": BrainstormerAgent,
            "web_searcher": WebSearcherAgent,
            "code_gen": CodeGenAgent,
            "general": GeneralAgent,
        }

        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")

        try:
            return agent_classes[agent_type](
                model_name=settings.model,
                api_key=settings.api_key,
                system_prompt=settings.system_prompt,
                temperature=settings.temperature,
                provider=settings.provider,
            )
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
