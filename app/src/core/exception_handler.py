from collections.abc import Callable
from typing import Any

import langgraph.errors as lg_errors

from app.src.core.messages import describe_error, http_status
from app.src.core.ui import AgentUI
from app.utils.logger import logger


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
        while True:
            try:
                return operation()

            except lg_errors.GraphRecursionError as e:
                if propagate:
                    raise

                logger.warning(f"Graph recursion error, retries: {retries}", exc_info=e)

                if retry_operation:
                    ui.warning(
                        "Agent processing took longer than expected (Max recursion limit reached)"
                    )
                    if retries >= AgentExceptionHandler.MAX_RETRIES:
                        logger.error(
                            f"Max retries ({AgentExceptionHandler.MAX_RETRIES}) reached",
                            exc_info=e,
                        )
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

            except Exception as e:
                if propagate:
                    raise

                if http_status(e) == 429:
                    logger.error("Rate limit exceeded", exc_info=e)
                    ui.error("Rate limit exceeded. Please try again later")
                    return None

                logger.exception("Unexpected error in agent operation")
                ui.error(f"An unexpected error occurred\n{describe_error(e)}")
                return None
