import os
import sqlite3
from collections.abc import Callable
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from app.src.core.messages import content_text
from app.src.core.permissions import PermissionDeniedException
from app.src.core.ui import default_ui
from app.utils.constants import LAST_N_TURNS
from app.utils.paths import data_dir
from app.utils.ui_messages import UI_MESSAGES


class State(TypedDict):
    """Common state structure for all agents."""

    messages: Annotated[list[BaseMessage], add_messages]


def tools_condition(
    state: State,
    messages_key: str = "messages",
) -> Literal["tools", "__end__"]:
    """Determine whether to call tools based on the presence of tool calls in the last AI message."""
    if isinstance(state, list):
        ai_message = state[-1]
    elif (isinstance(state, dict) and (messages := state.get(messages_key, []))) or (
        messages := getattr(state, messages_key, [])
    ):
        ai_message = messages[-1]
    else:
        msg = f"No messages found in input state to tool_edge: {state}"
        raise ValueError(msg)
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return "__end__"


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

        if total_tools > 1:
            default_ui.pending_tools(total_tools)

        for idx, tool_call in enumerate(tool_calls, start=1):
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

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
                denied = isinstance(e, PermissionDeniedException)
                if denied:
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

                if not self.handle_tool_errors and not denied:
                    raise

        return {"messages": result_messages}


_checkpointer: SqliteSaver | None = None


def get_checkpointer() -> SqliteSaver:
    """Return the chat history checkpointer shared by every agent."""
    global _checkpointer
    if _checkpointer is None:
        db_file = data_dir("history", "ALLY_HISTORY_DIR") / "history.sqlite"
        _checkpointer = SqliteSaver(sqlite3.connect(db_file, check_same_thread=False))
    return _checkpointer


OPENAI_COMPATIBLE_URLS = {
    "openai": None,
    "openrouter": "https://openrouter.ai/api/v1",
}


def create_chat_model(
    provider: str,
    model_name: str,
    api_key: str | None,
    temperature: float | None = None,
):
    """Return a LangChain chat model for ``provider``.

    Raises:
        ValueError: If the provider is not supported.
    """
    provider = provider.lower()
    options = {} if temperature is None else {"temperature": temperature}

    match provider:
        case "openai" | "openrouter":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=OPENAI_COMPATIBLE_URLS[provider],
                max_retries=5,
                **options,
            )
        case "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=model_name, api_key=api_key, max_retries=5, **options
            )
        case "google":
            os.environ.setdefault("GRPC_VERBOSITY", "NONE")
            os.environ.setdefault("GRPC_CPP_VERBOSITY", "NONE")

            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=model_name, google_api_key=api_key, max_retries=5, **options
            )
        case "groq":
            from langchain_groq import ChatGroq

            return ChatGroq(model=model_name, api_key=api_key, max_retries=5, **options)
        case "cerebras":
            from langchain_cerebras import ChatCerebras

            return ChatCerebras(
                model=model_name, api_key=api_key, max_retries=5, **options
            )
        case "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=model_name,
                validate_model_on_init=True,
                reasoning=False,
                **options,
            )
        case _:
            raise ValueError(f"Unsupported inference provider: {provider}")


def create_base_agent(
    model_name: str,
    api_key: str | None,
    tools: list,
    system_prompt: str,
    temperature: float | None = None,
    provider: str = "openai",
) -> CompiledStateGraph:
    """Build an agent graph that loops between the model and its tools.

    Args:
        model_name: Model identifier understood by the provider.
        api_key: API key for the provider, if it needs one.
        tools: Tools the model may call.
        system_prompt: System prompt sent with every request.
        temperature: Sampling temperature, or ``None`` for the provider's default.
        provider: Inference provider name, such as ``"openai"`` or ``"ollama"``.
    """
    llm = create_chat_model(provider, model_name, api_key, temperature)

    template = ChatPromptTemplate.from_messages(
        [SystemMessage(content=system_prompt), MessagesPlaceholder("messages")]
    )

    llm_with_tools = llm.bind_tools(tools) if tools else llm
    llm_chain = template | llm_with_tools
    graph = StateGraph(State)

    def llm_node(state: State):
        context = build_llm_context(state["messages"])
        return {"messages": [llm_chain.invoke({"messages": context})]}

    tool_node = SequentialToolNode(tools=tools, handle_tool_errors=True)

    graph.add_node("llm", llm_node)

    if tools:
        graph.add_node("tools", tool_node)
        graph.add_edge(START, "llm")
        graph.add_conditional_edges("llm", tools_condition)
        graph.add_edge("tools", "llm")
    else:
        graph.add_edge(START, "llm")
        graph.add_edge("llm", END)

    return graph.compile(checkpointer=get_checkpointer())


def build_llm_context(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Keep the current turn whole and trim the history that comes before it."""
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


def clean_context_window(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Condense earlier turns to the last ``LAST_N_TURNS`` user messages and their replies.

    Tool calls, tool results and retrieved RAG context from earlier turns are dropped, and
    replies are reduced to their text, so old turns stay small and never contain tool
    calls without matching results.
    """
    new_context: list[BaseMessage] = []
    replies: list[AIMessage] = []
    turn_count = 0

    for message in reversed(messages):
        if isinstance(message, HumanMessage) and not message.additional_kwargs.get(
            "RAG", False
        ):
            if turn_count == LAST_N_TURNS:
                break
            new_context.extend(replies)
            new_context.append(message)
            replies = []
            turn_count += 1

        elif isinstance(message, AIMessage):
            text = content_text(message.content)
            if text.strip():
                replies.append(AIMessage(content=text))

    new_context.reverse()
    return new_context
