import io

from langchain_core.messages import AIMessage
from rich.console import Console

from app.src.core.agent_factory import AgentFactory
from app.src.core.ui import AgentUI, ResponseStream
from app.src.orchestration.integrate_web_search import integrate_web_search


class RecordingStream:
    def __init__(self):
        self.tokens: list[str] = []

    def wait(self):
        pass

    def add(self, token):
        self.tokens.append(token)

    def close(self):
        pass


def test_reply_tokens_stream_but_nested_agent_tokens_do_not(
    fake_llm, settings, monkeypatch
):
    agent = AgentFactory.create_agent("general", settings)
    searcher = AgentFactory.create_agent("web_searcher", settings)
    integrate_web_search(agent, searcher)

    recorder = RecordingStream()
    shown: list[str] = []
    monkeypatch.setattr(agent.ui, "response_stream", lambda: recorder)
    monkeypatch.setattr(agent.ui, "ai_response", shown.append)
    monkeypatch.setattr(agent.ui, "tool_call", lambda *a, **k: None)
    monkeypatch.setattr(agent.ui, "tool_output", lambda *a, **k: None)

    fake_llm.replies += [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "call_searcher", "args": {"query": "news"}, "id": "1"}
            ],
        ),
        "nested research notes",
        "final answer for you",
    ]
    agent.configuration = {"configurable": {"thread_id": "t"}, "recursion_limit": 25}

    agent._run_turn([("human", "what is new?")], stream=True)

    streamed = "".join(recorder.tokens)
    assert "final answer for you" in streamed
    assert "nested" not in streamed
    assert shown == ["final answer for you"]


def test_response_stream_hides_reasoning_and_cleans_up():
    console = Console(file=io.StringIO(), force_terminal=True, width=80, height=20)
    stream = ResponseStream(AgentUI(console))

    stream.wait()
    stream.add("<think>private reasoning")
    assert stream._live is None

    stream.add("</think>Hello there")
    assert stream._live is not None
    assert "private" not in stream._render("Hello there").renderable.plain

    stream.close()
    assert stream._live is None
    assert stream._status is None
    assert stream.text == ""


def test_response_stream_is_silent_without_a_terminal():
    console = Console(file=io.StringIO(), force_terminal=False)
    stream = ResponseStream(AgentUI(console))

    stream.wait()
    stream.add("Hello")
    stream.close()

    assert console.file.getvalue() == ""
