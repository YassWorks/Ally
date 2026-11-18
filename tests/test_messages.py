from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.src.core.create_base_agent import build_llm_context, clean_context_window
from app.src.core.messages import content_text, describe_error, http_status
from app.utils.constants import LAST_N_TURNS


class ProviderError(Exception):
    def __init__(self, status_code):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


class Response:
    status_code = 429


class WrappedError(Exception):
    response = Response()


def test_content_text_handles_strings_and_blocks():
    blocks = [
        {"type": "text", "text": "Hello "},
        {"type": "tool_use", "id": "1", "name": "read_file", "input": {}},
        "world",
    ]

    assert content_text("plain") == "plain"
    assert content_text(blocks) == "Hello world"
    assert content_text(None) == ""
    assert content_text([]) == ""


def test_http_status():
    assert http_status(ProviderError(404)) == 404
    assert http_status(WrappedError()) == 429
    assert http_status(ValueError("nope")) is None


def test_describe_error_is_one_short_line():
    text = describe_error(RuntimeError("first line\nsecond line" + "x" * 500))

    assert text == "RuntimeError: first line"
    assert describe_error(RuntimeError("y" * 500)).endswith("...")


def anthropic_reply(text):
    return AIMessage(
        content=[
            {"type": "text", "text": text},
            {
                "type": "tool_use",
                "id": "t1",
                "name": "read_file",
                "input": {"file_path": "a"},
            },
        ],
        tool_calls=[{"name": "read_file", "args": {"file_path": "a"}, "id": "t1"}],
    )


def test_old_turns_keep_text_only():
    history = [
        HumanMessage("read a"),
        anthropic_reply("Reading it."),
        ToolMessage("contents", tool_call_id="t1"),
        AIMessage("Done."),
        HumanMessage("thanks"),
    ]

    context = build_llm_context(history)

    assert [type(m).__name__ for m in context] == [
        "HumanMessage",
        "AIMessage",
        "AIMessage",
        "HumanMessage",
    ]
    assert context[1].content == "Reading it."
    assert not context[1].tool_calls


def test_rag_context_from_old_turns_is_dropped():
    history = [
        HumanMessage("q1"),
        HumanMessage("doc text", additional_kwargs={"RAG": True}),
        AIMessage("a1"),
    ]

    assert [m.content for m in clean_context_window(history)] == ["q1", "a1"]


def test_context_keeps_exactly_the_last_n_turns():
    history = []
    for i in range(LAST_N_TURNS + 5):
        history += [HumanMessage(f"q{i}"), AIMessage(f"a{i}")]

    context = clean_context_window(history)
    questions = [m.content for m in context if isinstance(m, HumanMessage)]

    assert len(questions) == LAST_N_TURNS
    assert questions[-1] == f"q{LAST_N_TURNS + 4}"
    assert isinstance(context[0], HumanMessage)
