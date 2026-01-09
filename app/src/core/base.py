from app.utils.ascii_art import ASCII_ART
from app.utils.constants import RECURSION_LIMIT, PROMPTS
from app.src.core.exception_handler import AgentExceptionHandler
from app.src.core.permissions import PermissionDeniedException
from app.src.embeddings.rag_errors import SetupFailedError, DBAccessError
from app.utils.logger import logger
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage, HumanMessage
from app.src.embeddings.db_client import DataBaseClient
from langgraph.graph.state import CompiledStateGraph
from typing import Callable
from langgraph.graph import StateGraph
from app.src.core.ui import AgentUI
import langgraph.errors as lg_errors
from app.utils.ui_messages import UI_MESSAGES
import subprocess
import uuid
import os
import re
import openai


class BaseAgent:
    """Base class for all agent implementations.

    Provides common functionality including chat interface, model management,
    and message handling for agent interactions.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str,
        system_prompt: str,
        agent: CompiledStateGraph,
        ui: AgentUI,
        get_agent: Callable,
        temperature: float = 0,
        graph: StateGraph = None,
        provider: str = None,
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.agent = agent
        self.ui = ui
        self.get_agent = get_agent
        self.temperature = temperature
        self.graph = graph
        self.provider = provider

        # a dictionary to hold custom command names and handlers
        self._custom_commands: dict[str, Callable] = {}

        # a flag to determine if RAG features should be integrated
        self.rag = False

        self.latest_refs: set[str] = set()
        self.db_client = None

        # backup model name after failed `/model change` command
        self.prev_model_name = None

    def _toggle_rag(self, enable: bool = True):
        """Enable or disable RAG features."""
        self.rag = enable

    def get_session_id(self) -> str:
        """Get the current session/thread ID."""
        return self.configuration.get("configurable", {}).get("thread_id", "")

    def start_chat(
        self,
        starting_msg: str = None,
        initial_prompt_suffix: str = None,
        recurring_prompt_suffix: str = None,
        recursion_limit: int = RECURSION_LIMIT,
        thread_id: str = None,
        config: dict = None,
        show_welcome: bool = True,
        active_dir: str = None,
        stream: bool = True,
    ) -> bool:
        """Start interactive chat session with the agent."""

        if show_welcome:
            self.ui.logo(ASCII_ART)
            self.ui.help(self.model_name)

        self.configuration = config or {
            "configurable": {"thread_id": thread_id or str(uuid.uuid4())},
            "recursion_limit": recursion_limit,
        }

        continue_flag = False
        first_msg = True

        while True:
            try:
                if continue_flag:
                    self.ui.status_message(
                        title=UI_MESSAGES["titles"]["continuing_session"],
                        message=UI_MESSAGES["messages"]["continuing_session"],
                        style="primary",
                    )

                if first_msg and starting_msg:
                    user_input = starting_msg
                else:
                    user_input = self._get_user_input(
                        continue_flag=continue_flag,
                        active_dir=active_dir,
                    )

                continue_flag = False

                if not user_input:
                    continue

                if user_input.strip().lower() in ["/quit", "/exit", "/q"]:
                    self.ui.goodbye()
                    return True

                if self._handle_command(user_input, self.configuration):
                    continue

                if user_input.startswith("!"):
                    self._handle_shell_command(user_input[1:].strip())
                    continue

                if first_msg and initial_prompt_suffix:
                    user_input += f"\n\n{initial_prompt_suffix}"
                if recurring_prompt_suffix:
                    user_input += f"\n\n{recurring_prompt_suffix}"

                rag_final_message = None
                query_results = None
                extra_rag_context = ""

                with self.ui.console.status(
                    UI_MESSAGES["messages"]["querying_knowledge_base"]
                ):
                    if self.rag:
                        self.db_client = DataBaseClient.get_instance()
                        if self.db_client is None:
                            self.ui.warning(
                                UI_MESSAGES["warnings"]["rag_enabled_no_client"]
                            )
                        else:
                            query_results = self.db_client.get_query_results(
                                user_input, n_results=5
                            )
                            if query_results:
                                extra_rag_context += PROMPTS["rag_results"]
                                extra_rag_context += "\n".join(
                                    [f"- {doc}" for doc, _ in query_results]
                                )

                    if query_results:
                        self.latest_refs = {
                            meta["file_path"]
                            for _, meta in query_results
                            if meta and "file_path" in meta
                        }
                    else:
                        self.latest_refs = set()

                    if extra_rag_context:
                        rag_final_message = HumanMessage(
                            content=extra_rag_context,
                            additional_kwargs={
                                "RAG": True,
                            },
                        )

                last = None
                for chunk in self.agent.stream(
                    {
                        "messages": (
                            [("human", user_input), rag_final_message]
                            if rag_final_message
                            else [("human", user_input)]
                        )
                    },
                    config=self.configuration,
                ):
                    if stream:
                        self._display_chunk(chunk)
                    last = chunk
                if not stream:
                    self._display_chunk(last)

            except KeyboardInterrupt:
                self.ui.goodbye()
                return True

            except openai.NotFoundError as e:
                logger.error(f"Model not found: {self.model_name}", exc_info=e)
                self.ui.error(
                    UI_MESSAGES["errors"]["model_not_found"]
                )
                if self.prev_model_name:
                    self.ui.status_message(
                        title=UI_MESSAGES["titles"]["reverting_model"],
                        message=f"Reverting to previous model: {self.prev_model_name}",
                    )
                    self.model_name = self.prev_model_name
                    self._handle_model_change(self.model_name)
                    self.prev_model_name = None
                else:
                    if self.ui.confirm(
                        UI_MESSAGES["confirmations"]["change_model"], default=True
                    ):
                        new_model = self.ui.get_input(
                            message="Enter new model name: ",
                        ).strip()
                        if new_model:
                            self.prev_model_name = self.model_name
                            self.model_name = new_model
                            self._handle_model_change(self.model_name)
                    else:
                        self.ui.goodbye()
                        return True

            except PermissionDeniedException:
                continue  # Do nothing. Let the user enter a new prompt.

            except lg_errors.GraphRecursionError as e:
                logger.warning("Graph recursion limit reached", exc_info=e)
                self.ui.warning(UI_MESSAGES["warnings"]["recursion_limit_reached"])
                if self.ui.confirm(
                    UI_MESSAGES["confirmations"]["continue_from_left_off"], default=True
                ):
                    continue_flag = True
                else:
                    return False

            except openai.RateLimitError as e:
                logger.error("OpenAI rate limit exceeded", exc_info=e)
                self.ui.error(UI_MESSAGES["errors"]["rate_limit_exceeded"])
                if self.ui.confirm(
                    UI_MESSAGES["confirmations"]["change_model"], default=True
                ):
                    new_model = self.ui.get_input(
                        message="Enter new model name: ",
                    ).strip()
                    if new_model:
                        self.model_name = new_model
                        self._handle_model_change(self.model_name)
                else:
                    self.ui.goodbye()
                    return True

            except Exception as e:
                logger.exception("Unexpected error in chat loop")
                self.ui.error(UI_MESSAGES["errors"]["unexpected_error"])
                return False

            finally:
                first_msg = False

    def _handle_shell_command(self, command: str):
        """Handle execution of shell commands."""
        import shutil

        logger.debug(f"Executing shell command: {command}")

        shell_name = None

        if os.name == "nt":
            # check for powershell first, if it exists use it
            if shutil.which("pwsh") or shutil.which("pwsh.exe"):  # Powershell 7
                shell_name = "pwsh.exe"
            elif shutil.which("powershell") or shutil.which("powershell.exe"):  # Powershell 5
                shell_name = "powershell.exe"
            else:
                shell_name = "cmd.exe"
        else:
            # for UNIX-like it's straightforward, use the default shell or sh
            shell_name = os.environ.get("SHELL", "/bin/sh")

        # all standard shells use -c to execute commands
        # except for cmd.exe which uses /c without opening a new terminal
        flag = "/c" if shell_name == "cmd.exe" else "-c"
        full_command = f'{shell_name} {flag} "{command}"'

        try:
            result = self._execute_shell_command(full_command)
            logger.info(f"Command executed successfully: {command}")
            if str(result.stdout).strip():
                print(str(result.stdout).strip())
            else:
                self.ui.print("No output returned from the command.", color="dim")
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Shell command failed with exit code {e.returncode}: {command}",
                exc_info=e,
            )
            error_msg = e.stderr.strip() if e.stderr else str(e)
            self.ui.error(f"An error occurred: {error_msg}")
        except Exception as e:
            logger.exception(f"Unexpected error executing shell command: {command}")
            self.ui.error(f"An unexpected error occurred: {str(e)}")

        return True

    def _execute_shell_command(self, command: str) -> subprocess.CompletedProcess:
        """Execute a shell command and display the output."""
        logger.debug(f"Full command to execute: {command}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            shell=True,  # full freedom
            cwd=os.getcwd(),
        )
        return result

    def _get_user_input(
        self, continue_flag: bool = False, active_dir: str = None
    ) -> str:
        """Get user input, handling continuation scenarios."""
        if continue_flag:
            return PROMPTS["continue"]
        else:
            return self.ui.get_input(
                model=self.model_name,
                cwd=active_dir or os.getcwd(),
            ).strip()

    def _handle_command(self, user_input: str, configuration: dict) -> bool:
        """Handle chat commands. Returns True if command was processed."""

        if user_input.strip().lower() == "/clear":
            configuration["configurable"]["thread_id"] = str(uuid.uuid4())
            self.ui.history_cleared()
            return True

        if user_input.strip().lower() in ["/cls", "/clearterm", "/clearscreen"]:
            os.system("cls" if os.name == "nt" else "clear")
            return True

        if user_input.strip().lower() in ["/help", "/h"]:
            self.ui.help(self.model_name)
            return True

        if user_input.strip().lower().startswith("/model"):
            self._handle_model_command(user_input)
            return True

        if user_input.strip().lower().startswith("/id"):
            parts = user_input.split()
            if len(parts) == 1:
                self.ui.status_message(
                    title=UI_MESSAGES["titles"]["current_session_id"],
                    message=self.get_session_id(),
                )
                return True
            else:
                new_id = parts[1]
                self.configuration["configurable"]["thread_id"] = new_id
                self.ui.status_message(
                    title=UI_MESSAGES["titles"]["changed_session_id"],
                    message=f"Session ID changed to: {new_id}",
                )
                return True

        if user_input.strip().lower() in ["/refs", "/references"]:
            if self.latest_refs:
                self.ui.status_message(
                    title=UI_MESSAGES["titles"]["latest_references"],
                    message="\n".join(self.latest_refs),
                    style="primary",
                )
            else:
                self.ui.status_message(
                    title=UI_MESSAGES["titles"]["latest_references"],
                    message=UI_MESSAGES["messages"]["no_references"],
                    style="muted",
                )
            return True

        for cmd, handler in self._custom_commands.items():
            cmd_parts = user_input.split()
            if cmd_parts[0].lower() == cmd:
                try:
                    handler(*(cmd_parts[1:] if len(cmd_parts) > 1 else []))

                except DBAccessError:
                    self.ui.error(UI_MESSAGES["errors"]["db_access_error"])
                    self.ui.warning(UI_MESSAGES["warnings"]["rag_features_disabled"])
                    self.rag = False

                except SetupFailedError:
                    self.ui.error(UI_MESSAGES["errors"]["setup_failed"])
                    self.ui.warning(UI_MESSAGES["warnings"]["rag_features_disabled"])
                    self.rag = False

                except Exception as e:
                    logger.exception(f"Command failed: {cmd}")
                    self.ui.error(
                        UI_MESSAGES["errors"]["command_failed"]
                    )

                finally:
                    return True

        if user_input.lower().startswith("/"):
            self.ui.error(UI_MESSAGES["errors"]["unknown_command"])
            return True

        return False

    def _handle_model_change(self, new_model: str):
        """Handle changing the model."""
        graph, agent = self.get_agent(
            model_name=new_model,
            api_key=self.api_key,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            include_graph=True,
            provider=self.provider,
        )
        self.graph = graph
        self.agent = agent

    def _handle_model_command(self, user_input: str):
        """Handle model-related commands."""
        command_parts = user_input.lower().split(" ")

        if len(command_parts) == 1:
            self.ui.status_message(
                title=UI_MESSAGES["titles"]["current_model"],
                message=self.model_name,
            )
            return

        if command_parts[1] == "change":
            if len(command_parts) < 3:
                self.ui.error(UI_MESSAGES["errors"]["specify_model"])
                return

            new_model = command_parts[2]
            self.ui.status_message(
                title=UI_MESSAGES["titles"]["change_model"],
                message=f"Changing model to {new_model}",
            )

            self.prev_model_name = self.model_name
            self.model_name = new_model

            self._handle_model_change(self.model_name)
            return

        self.ui.error(UI_MESSAGES["errors"]["unknown_model_command"])

    def invoke(
        self,
        message: str,
        recursion_limit: int = RECURSION_LIMIT,
        config: dict = None,
        extra_context: str | list[str] = None,
        include_thinking_block: bool = False,
        stream: bool = False,
        intermediary_chunks: bool = False,
        quiet: bool = False,
        propagate_exceptions: bool = False,
        active_dir: str = None,
    ):
        """Invoke agent with a message and return response."""

        configuration = config or {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": recursion_limit,
        }

        if extra_context:
            message = self._add_extra_context(message, extra_context)

        def execute_agent(message):
            if stream:
                last = None
                for chunk in self.agent.stream(
                    {"messages": [("human", message)]},
                    config=configuration,
                ):
                    if not quiet:
                        self._display_chunk(chunk)
                    last = chunk
                return last.get("llm", {}) if last else {}
            else:
                return self.agent.invoke(
                    {"messages": [("human", message)]},
                    config=configuration,
                )

        raw_response = AgentExceptionHandler.handle_agent_exceptions(
            operation=lambda: execute_agent(message),
            ui=self.ui,
            propagate=propagate_exceptions,
            continue_on_limit=False,
            retry_operation=lambda: execute_agent(PROMPTS["continue"]),
            reject_operation=lambda: execute_agent(
                self._get_user_input(active_dir=active_dir)
            ),
        )

        if raw_response is None:
            return UI_MESSAGES["errors"]["agent_execution_failed"]

        if intermediary_chunks and not quiet:
            for chunk in raw_response.get("messages", []):
                self._display_chunk(chunk)

        ret = self._extract_response_content(raw_response)

        if not include_thinking_block:
            ret = self._remove_thinking_block(ret)

        return ret

    def _add_extra_context(self, message: str, extra_context: str | list[str]) -> str:
        """Add extra context to the message."""
        if isinstance(extra_context, str):
            return f"{message}\n\nExtra context you must know:\n{extra_context}"
        elif isinstance(extra_context, list):
            return f"{message}\n\nExtra context you must know:\n" + "\n".join(
                extra_context
            )
        return message

    def _extract_response_content(self, raw_response: dict) -> str:
        """Extract content from agent response."""
        messages = raw_response.get("messages", [])
        if (
            messages
            and isinstance(messages[-1], AIMessage)
            and hasattr(messages[-1], "content")
        ):
            return messages[-1].content.strip()
        return UI_MESSAGES["errors"]["no_messages_returned"]

    def _remove_thinking_block(self, content: str) -> str:
        """Remove thinking block from response content."""
        return re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL)

    def _display_chunk(self, chunk: BaseMessage | dict):
        """Display chunk content in the UI."""
        if isinstance(chunk, BaseMessage):
            if isinstance(chunk, AIMessage):
                self._handle_ai_message(chunk)
            elif isinstance(chunk, ToolMessage):
                self._handle_tool_message(chunk)
        elif isinstance(chunk, dict):
            self._handle_dict_chunk(chunk)

    def _handle_dict_chunk(self, chunk: dict):
        """Handle dictionary chunk format."""
        llm_data = chunk.get("llm", {})
        if "messages" in llm_data:
            messages = llm_data["messages"]
            if messages and isinstance(messages[0], AIMessage):
                self._handle_ai_message(messages[0])

        tools_data = chunk.get("tools", {})
        if "messages" in tools_data:
            for tool_message in tools_data["messages"]:
                self._handle_tool_message(tool_message)

    def _handle_ai_message(self, message: AIMessage):
        """Handle AI message display."""
        if message.content and message.content.strip():
            # remove thinking blocks before displaying
            content = self._remove_thinking_block(message.content)
            self.ui.ai_response(content)

    def _handle_tool_message(self, message: ToolMessage):
        """Handle tool message display."""
        self.ui.tool_output(message.name, message.content)

    def register_command(self, name: str, handler: Callable) -> None:
        self._custom_commands[name.lower()] = handler

    def unregister_command(self, name: str) -> None:
        self._custom_commands.pop(name.lower(), None)
