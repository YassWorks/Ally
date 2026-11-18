from abc import ABC, abstractmethod
from typing import Any

from app.src.core.base import BaseAgent
from app.src.core.ui import default_ui
from app.utils.constants import RECURSION_LIMIT


class BaseUnit(ABC):
    """Base class for orchestration units that coordinate multiple agents."""

    def __init__(self, agents: dict[str, BaseAgent]):
        """Initialize the unit with required agents.

        Args:
            agents: Dictionary of agent instances
        """
        self.agents = agents
        self.ui = default_ui
        self._validate_agents()

    @abstractmethod
    def _validate_agents(self):
        """Validate that all required agents are present and properly initialized."""
        pass

    @abstractmethod
    def run(self, **kwargs) -> bool:
        """Run the workflow and return whether it completed."""
        pass

    def _create_agent_config(
        self, thread_id: str, recursion_limit: int = RECURSION_LIMIT
    ) -> dict[str, Any]:
        """Create standardized configuration for agent operations.

        Args:
            thread_id: Unique identifier for the conversation thread
            recursion_limit: Maximum recursion depth

        Returns:
            Configuration dictionary
        """
        return {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": recursion_limit,
        }
