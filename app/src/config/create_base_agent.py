from langchain_cerebras import ChatCerebras
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path
import sqlite3


class State(TypedDict):
    """Common state structure for all agents."""
    messages: Annotated[list[BaseMessage], add_messages]
    
    
LAST_N_TURNS = 20


def create_base_agent(
    model_name: str,
    api_key: str,
    tools: list,
    system_prompt: str,
    temperature: float = 0,
    include_graph: bool = False,
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

    llm = ChatCerebras(
        model=model_name,
        temperature=temperature,
        timeout=None,
        max_retries=5,
        api_key=api_key,
    )

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

    def forward(state: State):
        return {}
    
    def toolcall_error(state: State):
        error_message = HumanMessage(
            content="Error: Your tool call was malformed or non-JSON. Please fix and retry.",
        )
        return {"messages": [error_message]}

    graph.add_node("llm", llm_node)
    graph.add_node("tools", tool_node)
    graph.add_node("toolcall_checker", forward)
    graph.add_node("toolcall_error", toolcall_error)

    if tools:
        graph.add_edge(START, "llm")
        graph.add_conditional_edges("llm", tool_call_attempted)
        graph.add_conditional_edges("toolcall_checker", valid_toolcall)
        graph.add_edge("toolcall_error", "llm")
        graph.add_edge("tools", "llm")
    else:
        graph.add_edge(START, "llm")
        graph.add_edge("llm", END)

    db_path = (Path(__file__).resolve().parents[2] / "database")
    db_file = db_path / "memory.sqlite"
    conn = sqlite3.connect(db_file.as_posix(), check_same_thread=False)

    mem = SqliteSaver(conn)
    built_graph = graph.compile(checkpointer=mem)

    if include_graph:
        return graph, built_graph
    else:
        return built_graph


def tool_call_attempted(state: State):
    """Check if the agent attempted to make a tool call."""

    if state["messages"]:
        ai_message = state["messages"][-1]
        content = ai_message.content
        tool_calls = getattr(ai_message, "tool_calls", None)
    else:
        raise ValueError("No messages found in input state to check for tool calls.")

    content = flatten_content(content)

    # checking if tool calls were made or if it looks like the agent tried to make one
    if tool_calls or any(
        substr in content for substr in ("tool_call", "arguments", "<tool", "tool>")
    ):
        return "toolcall_checker"
    else:
        return END


def valid_toolcall(state: State):
    """Validate tool calls and handle malformed ones."""

    if state["messages"]:
        ai_message = state["messages"][-1]
        content = ai_message.content
        tool_calls = getattr(ai_message, "tool_calls", None)
    else:
        raise ValueError("No messages found in input state to check for tool calls.")

    content = flatten_content(content)

    # checking for malformed tool calls inside the content block
    if not tool_calls and any(
        substr in content for substr in ("tool_call", "arguments", "<tool", "tool>")
    ):
        return "toolcall_error"
    else:
        return "tools"


def build_llm_context(messages: list[BaseMessage]):
    """
    Build the context for the LLM by including all messages after the last human message.
    And cleaning off anything before it.
    """
    new_context = []
    last_human_idx = len(messages)-1
    
    for i in range(len(messages)-1, -1, -1):
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
            if hasattr(message, "content") and flatten_content(message.content).strip() != "":
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
    if isinstance(content, list):
        if isinstance(content[0], dict):
            content = "\n".join([f"{k}: {v}" for item in content for k, v in item.items()])
        if isinstance(content[0], str):
            content = "\n".join(content)
    return content
