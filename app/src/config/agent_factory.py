from typing import Dict, Any, Optional
from app.src.agents.brainstormer.brainstormer import BrainstormerAgent
from app.src.agents.web_searcher.web_searcher import WebSearcherAgent
from app.src.agents.code_gen.code_gen import CodeGenAgent
from app.src.agents.general.general import GeneralAgent


class AgentFactory:
    """Factory for creating and managing agent instances."""

    @staticmethod
    def create_agent(agent_type: str, config: Dict[str, Any]) -> Any:
        """Create an agent instance based on type and configuration.

        Args:
            agent_type: Type of agent to create ('brainstormer', 'web_searcher', 'code_gen')
            config: Configuration dictionary with required parameters

        Returns:
            Agent instance

        Raises:
            ValueError: If agent type is unknown or required config is missing
            RuntimeError: If agent initialization fails
        """

        required_fields = ["model_name", "api_key"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")

        agent_classes = {
            "brainstormer": BrainstormerAgent,
            "web_searcher": WebSearcherAgent,
            "code_gen": CodeGenAgent,
            "general": GeneralAgent
        }

        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")

        try:
            return agent_classes[agent_type](
                model_name=config["model_name"],
                api_key=config["api_key"],
                system_prompt=config.get("system_prompt", None),
                temperature=config.get("temperature", 0),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize {agent_type} agent: {e}")

    @staticmethod
    def create_coding_agents(
        model_names: Dict[str, str],
        api_keys: Dict[str, str],
        temperatures: Optional[Dict[str, float]] = None,
        system_prompts: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create all agents needed for coding.

        Args:
            model_names: Dictionary mapping agent names to model names
            api_keys: Dictionary mapping agent names to API keys
            temperatures: Optional temperature settings for each agent
            system_prompts: Optional system prompts for each agent

        Returns:
            Dictionary of initialized agents
        """

        agents = {}
        agent_types = ["brainstormer", "web_searcher", "code_gen"]

        for agent_type in agent_types:
            config = {
                "model_name": model_names[agent_type],
                "api_key": api_keys[agent_type],
                "temperature": (temperatures or {}).get(agent_type, 0),
                "system_prompt": (system_prompts or {}).get(agent_type),
            }
            agents[agent_type] = AgentFactory.create_agent(agent_type, config)

        return agents
