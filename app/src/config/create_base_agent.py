from app.utils.constants import DEFAULT_PATHS
from app.src.helpers.valid_dir import validate_dir_name
from app.src.config.ui import default_ui
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path
import sqlite3
import os


class State(TypedDict):
    """Common state structure for all agents."""

    messages: Annotated[list[BaseMessage], add_messages]


LAST_N_TURNS = 10
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

    try:
        match provider:
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
                from langchain_google_genai import ChatGoogleGenerativeAI

                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=temperature,
                    timeout=None,
                    max_retries=5,
                    google_api_key=api_key,
                )
            case "openai":
                from langchain_openai import ChatOpenAI

                llm = ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    timeout=None,
                    max_retries=5,
                    api_key=api_key,
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

    except Exception as e:
        from rich.console import Console
        from app.src.config.ui import AgentUI
        from app.utils.constants import CONSOLE_WIDTH

        ui = AgentUI(console=Console(width=CONSOLE_WIDTH))
        ui.error(f"Failed to create LLM instance: {e}")

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

    tool_node = ToolNode(tools=tools, handle_tool_errors=False)

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


def build_llm_context(messages: list[BaseMessage]):
    """
    Build the context for the LLM by including all messages after the last human message.
    And cleaning off anything before it.
    """
    new_context = []
    last_human_idx = len(messages) - 1

    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage):
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

        if isinstance(message, HumanMessage):
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
