from app.utils.constants import DEFAULT_PATHS, LAST_N_TURNS
from app.src.helpers.valid_dir import validate_dir_name
from app.src.core.ui import default_ui
from app.utils.ui_messages import UI_MESSAGES
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated, Callable
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path
import sqlite3
import os


class State(TypedDict):
    """Common state structure for all agents."""

    messages: Annotated[list[BaseMessage], add_messages]


class SequentialToolNode:
    """A custom tool node that processes tool calls one at a time.

    This prevents UI collisions when multiple tools require permission
    confirmation by processing them sequentially instead of in parallel.
    """

    def __init__(self, tools: list, handle_tool_errors: bool = False):
        self.tools_by_name: dict[str, Callable] = {tool.name: tool for tool in tools}
        self.handle_tool_errors = handle_tool_errors

    def __call__(self, state: State) -> dict:
        """Process tool calls from the last AI message sequentially."""
        messages = state.get("messages", [])
        if not messages:
            return {"messages": []}

        # Find the last AI message with tool calls
        last_ai_message = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                last_ai_message = msg
                break

        if not last_ai_message or not last_ai_message.tool_calls:
            return {"messages": []}

        tool_calls = last_ai_message.tool_calls
        total_tools = len(tool_calls)
        result_messages = []

        # Show pending tools notification if more than 1
        if total_tools > 1:
            default_ui.pending_tools(total_tools)

        # Process each tool call one at a time
        for idx, tool_call in enumerate(tool_calls, start=1):
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            # Show progress if multiple tools
            if total_tools > 1:
                default_ui.processing_tool(idx, total_tools, tool_name, tool_args)

            default_ui.tool_call(tool_name, tool_args)

            tool = self.tools_by_name.get(tool_name)
            if tool is None:
                result_messages.append(
                    ToolMessage(
                        content=f"Tool '{tool_name}' not found.",
                        name=tool_name,
                        tool_call_id=tool_call_id,
                    )
                )
                continue

            try:
                # Execute the tool (this will trigger the permission check inside the tool)
                result = tool.invoke(tool_args)
                result_messages.append(
                    ToolMessage(
                        content=str(result),
                        name=tool_name,
                        tool_call_id=tool_call_id,
                    )
                )
            except Exception as e:
                error_content = f"Error: {e}"
                # Check if it's a permission denied exception
                if "PermissionDeniedException" in type(e).__name__:
                    error_content = UI_MESSAGES["tool"]["permission_denied"].format(
                        tool_name
                    )

                result_messages.append(
                    ToolMessage(
                        content=error_content,
                        name=tool_name,
                        tool_call_id=tool_call_id,
                    )
                )

                # Re-raise if not handling errors and it's not a permission issue
                if (
                    not self.handle_tool_errors
                    and "PermissionDeniedException" not in type(e).__name__
                ):
                    raise

        return {"messages": result_messages}


_PATH_ERROR_PRINTED = False


def create_base_agent(
    model_name: str,
    api_key: str,
    tools: list,
    system_prompt: str,
    temperature: float = 0,
    include_graph: bool = False,
    provider: str = None,
) -> CompiledStateGraph | tuple[StateGraph, CompiledStateGraph]:
    """Create a base agent with common configuration and error handling.

    Args:
        model_name: The name of the model to use
        api_key: The API key for the model
        tools: List of tools to be used by the agent
        system_prompt: System prompt for the agent
        temperature: Temperature for the model
        include_graph: Whether to include the graph in the response

    Returns:
        Compiled state graph agent or tuple of (graph, compiled_graph)
    """
    llm = None

    match provider.lower():
        case "groq":
            from langchain_groq import ChatGroq

            llm = ChatGroq(
                model=model_name,
                temperature=temperature,
                timeout=None,
                max_retries=5,
                api_key=api_key,
            )
        case "cerebras":
            from langchain_cerebras import ChatCerebras

            llm = ChatCerebras(
                model=model_name,
                temperature=temperature,
                timeout=None,
                max_retries=5,
                api_key=api_key,
            )
        case "ollama":
            from langchain_ollama import ChatOllama

            llm = ChatOllama(
                model=model_name,
                temperature=temperature,
                validate_model_on_init=True,
                reasoning=False,
            )
        case "google":
            os.environ["GRPC_VERBOSITY"] = "NONE"
            os.environ["GRPC_CPP_VERBOSITY"] = "NONE"

            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                timeout=None,
                max_retries=5,
                google_api_key=api_key,
            )
        case "openai" | "openrouter" | "github":
            from langchain_openai import ChatOpenAI

            if provider.lower() == "openai":
                base_url = None
            elif provider.lower() == "openrouter":
                base_url = "https://openrouter.ai/api/v1"
            else:  # github
                base_url = "https://models.github.ai/inference"

            llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                timeout=None,
                max_retries=5,
                api_key=api_key,
                base_url=base_url,
            )
        case "anthropic":
            from langchain_anthropic import ChatAnthropic

            llm = ChatAnthropic(
                model=model_name,
                temperature=temperature,
                timeout=None,
                max_retries=5,
                api_key=api_key,
            )
        case _:
            raise ValueError(f"Unsupported inference provider: {provider}")

    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("placeholder", "{messages}"),
        ]
    )

    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm
    llm_chain = template | llm_with_tools
    graph = StateGraph(State)

    def llm_node(state: State):
        context = build_llm_context(state["messages"])
        return {"messages": [llm_chain.invoke({"messages": context})]}

    tool_node = SequentialToolNode(tools=tools, handle_tool_errors=False)

    graph.add_node("llm", llm_node)

    if tools:
        graph.add_node("tools", tool_node)
        graph.add_edge(START, "llm")
        graph.add_conditional_edges("llm", tools_condition)
        graph.add_edge("tools", "llm")
    else:
        graph.add_edge(START, "llm")
        graph.add_edge("llm", END)

    db_path = ""
    if "ALLY_HISTORY_DIR" in os.environ:
        db_path = Path(os.getenv("ALLY_HISTORY_DIR"))
        if not validate_dir_name(str(db_path)):
            db_path = ""
            global _PATH_ERROR_PRINTED
            if not _PATH_ERROR_PRINTED:
                default_ui.warning(
                    "Invalid directory path found in $ALLY_HISTORY_DIR. Reverting to default path."
                )
                _PATH_ERROR_PRINTED = True

    if not db_path:
        db_path = DEFAULT_PATHS["history"]
        if os.name == "nt":
            db_path = Path(os.path.expandvars(db_path))
        else:
            db_path = Path(os.path.expanduser(db_path))

    db_file = db_path / "history.sqlite"

    if not db_path.exists():
        db_path.mkdir(parents=True, exist_ok=True)

    if not db_file.exists():
        db_file.touch()

    conn = sqlite3.connect(db_file.as_posix(), check_same_thread=False)
    mem = SqliteSaver(conn)

    built_graph = graph.compile(checkpointer=mem)

    if include_graph:
        return graph, built_graph
    else:
        return built_graph


def build_llm_context(messages: list[BaseMessage]) -> list[BaseMessage]:
    """
    Build the context for the LLM by including all messages after the last human message.
    And cleaning off anything before it.
    """
    new_context = []
    last_human_idx = len(messages) - 1

    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage) and not messages[
            i
        ].additional_kwargs.get("RAG", False):
            last_human_idx = i
            break

    new_context.extend(clean_context_window(messages[:last_human_idx]))
    new_context.extend(messages[last_human_idx:])

    return new_context


def clean_context_window(messages: list[BaseMessage]):
    """
    Clean the context window by keeping only the last N turns.
    And truncating the tools arguments for brevity.
    """
    new_context = []
    turn_count = 0

    for message in reversed(messages):

        if isinstance(message, HumanMessage) and not message.additional_kwargs.get(
            "RAG", False
        ):
            new_context.append(message)
            turn_count += 1
            if turn_count > LAST_N_TURNS:
                break

        elif isinstance(message, AIMessage):
            # strip all the tool_call related content for token efficiency
            if (
                hasattr(message, "content")
                and flatten_content(message.content).strip() != ""
            ):
                new_assistant_message = AIMessage(
                    content=message.content,
                )
                new_context.append(new_assistant_message)

    new_context.reverse()
    return new_context


def flatten_content(content: list[str | dict]) -> str:
    """
    Flatten the content by joining strings or formatting dictionaries.
    """
    try:
        if isinstance(content, list):
            if isinstance(content[0], dict):
                content = "\n".join(
                    [f"{k}: {v}" for item in content for k, v in item.items()]
                )
            if isinstance(content[0], str):
                content = "\n".join(content)
        return content
    except Exception:
        return str(content)
