from app.src.config.permissions import PermissionDeniedException
from app.src.config.ui import AgentUI
from typing import Callable, Any
import langgraph.errors as lg_errors
import openai


class AgentExceptionHandler:
    """Centralized exception handling for agent operations."""

    MAX_RETRIES = 50

    @staticmethod
    def handle_agent_exceptions(
        operation: Callable,
        ui: AgentUI,
        propagate: bool = False,
        continue_on_limit: bool = False,
        retries: int = 0,
    retry_operation: Callable | None = None,
    ) -> Any:

        try:
            return operation()

        except PermissionDeniedException:
            if propagate:
                raise

            ui.error("Permission denied")
            return None

        except lg_errors.GraphRecursionError:
            if propagate:
                raise

            ui.warning("Agent processing took longer than expected (Max recursion limit reached)")
            if retries >= AgentExceptionHandler.MAX_RETRIES:
                ui.status_message(
                    title="Max Retries Reached",
                    message="Please try again later.",
                    style="warning",
                )
                return None
        
            if continue_on_limit and ui.confirm(
                "Continue from where the agent left off?", default=True
            ):
                next_operation = retry_operation or operation
                return AgentExceptionHandler.handle_agent_exceptions(
                    operation=next_operation,
                    ui=ui,
                    propagate=propagate,
                    continue_on_limit=continue_on_limit,
                    retries=retries + 1,
                    retry_operation=retry_operation,
                )
            return None

        except openai.RateLimitError:
            if propagate:
                raise

            ui.error("Rate limit exceeded. Please try again later")
            return None

        except Exception as e:
            if propagate:
                raise

            ui.error(f"An unexpected error occurred: {e}")
            return None
