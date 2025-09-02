from abc import ABC, abstractmethod
from typing import Any
from app.src.config.ui import AgentUI
from rich.console import Console
from app.utils.constants import CONSOLE_WIDTH
from app.src.config.base import BaseAgent


class BaseUnit(ABC):
    """Base class for orchestration units that coordinate multiple agents."""
    
    def __init__(self, agents: dict[str, BaseAgent]):
        """Initialize the unit with required agents.
        
        Args:
            agents: Dictionary of agent instances
        """
        self.agents = agents
        self.console = Console(width=CONSOLE_WIDTH)
        self.ui = AgentUI(self.console)
        self._validate_agents()
    
    @abstractmethod
    def _validate_agents(self):
        """Validate that all required agents are present and properly initialized."""
        pass
    
    @abstractmethod
    def run(self, **kwargs) -> bool:
        """Execute the unit's main workflow.
        
        Returns:
            bool: True if execution completed successfully, False otherwise
        """
        pass
    
    def _setup_working_directory(self, default_dir: str = None) -> str:
        """Setup and validate working directory with user interaction.
        
        Args:
            default_dir: Default directory to use
            
        Returns:
            str: Validated working directory path
        """
        import os
        
        working_dir = default_dir or os.getcwd()
        
        while True:
            try:
                working_dir = self.ui.get_input(
                    message="Enter project directory",
                    default=working_dir,
                    cwd=working_dir,
                )
                os.makedirs(working_dir, exist_ok=True)
                return working_dir
            except Exception:
                self.ui.error("Failed to create project directory")
                working_dir = None
    
    def _create_agent_config(self, thread_id: str, recursion_limit: int = 100) -> dict[str, Any]:
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
