from app.src.core.permissions import PermissionDeniedException
from app.src.core.ui import AgentUI
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
        reject_operation: Callable | None = None,
    ) -> Any:
        while True:
            try:
                return operation()

            except PermissionDeniedException:
                if propagate:
                    raise
                
                if reject_operation:
                    operation = reject_operation
                    continue

                ui.error("Permission denied")
                return None

            except lg_errors.GraphRecursionError:
                if propagate:
                    raise
                
                if retry_operation:
                    ui.warning(
                        "Agent processing took longer than expected (Max recursion limit reached)"
                    )
                    if retries >= AgentExceptionHandler.MAX_RETRIES:
                        ui.status_message(
                            title="Max Retries Reached",
                            message="Agent has been running for a while now. Please make the necessary adjustments to your prompt.",
                            style="warning",
                        )
                        return None

                    if continue_on_limit and ui.confirm(
                        "Continue from where the agent left off?", default=True
                    ):
                        operation = retry_operation
                        retries += 1
                        continue
                
                ui.error("Max recursion limit reached. Operation cannot continue.")
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
