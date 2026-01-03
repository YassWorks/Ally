from app.src.core.permissions import PermissionDeniedException
from app.src.core.ui import AgentUI
from app.utils.logger import logger
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

            except PermissionDeniedException as e:
                if propagate:
                    raise
                
                logger.warning("Permission denied for operation", exc_info=e)
                
                if reject_operation:
                    operation = reject_operation
                    continue

                ui.error("Permission denied")
                return None

            except lg_errors.GraphRecursionError as e:
                if propagate:
                    raise
                
                logger.warning(f"Graph recursion error, retries: {retries}", exc_info=e)
                
                if retry_operation:
                    ui.warning(
                        "Agent processing took longer than expected (Max recursion limit reached)"
                    )
                    if retries >= AgentExceptionHandler.MAX_RETRIES:
                        logger.error(f"Max retries ({AgentExceptionHandler.MAX_RETRIES}) reached")
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

            except openai.RateLimitError as e:
                if propagate:
                    raise

                logger.error("OpenAI rate limit exceeded", exc_info=e)
                ui.error("Rate limit exceeded. Please try again later")
                return None

            except Exception as e:
                if propagate:
                    raise

                logger.exception("Unexpected error in agent operation")
                ui.error("An unexpected error occurred")
                return None
