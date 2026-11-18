import pytest
from langchain_core.messages import AIMessage

from app.src.core.agent_factory import AgentFactory
from app.src.core.ui import default_ui


class ProviderError(Exception):
    def __init__(self, status_code, message="boom"):
        super().__init__(message)
        self.status_code = status_code


@pytest.fixture
def chat(fake_llm, settings, monkeypatch):
    agent = AgentFactory.create_agent("brainstormer", settings)
    inputs: list[str] = []
    shown: list[str] = []
    errors: list[str] = []

    monkeypatch.setattr(agent.ui, "get_input", lambda *a, **k: inputs.pop(0))
    monkeypatch.setattr(agent.ui, "ai_response", shown.append)
    monkeypatch.setattr(agent.ui, "error", errors.append)
    monkeypatch.setattr(agent.ui, "goodbye", lambda: None)

    def run(*lines, confirm=True):
        inputs.extend(lines)
        monkeypatch.setattr(agent.ui, "confirm", lambda *a, **k: confirm)
        return agent.start_chat(show_welcome=False)

    return run, shown, errors


def test_list_content_from_anthropic_or_gemini_is_displayed(chat, fake_llm):
    run, shown, errors = chat
    fake_llm.replies.append(AIMessage(content=[{"type": "text", "text": "Hi there"}]))

    assert run("hello", "/q") is True
    assert shown == ["Hi there"]
    assert errors == []


def test_session_survives_a_failed_request(chat, fake_llm):
    run, shown, errors = chat
    fake_llm.failures.append(ProviderError(500, "server exploded"))
    fake_llm.replies.append("Recovered.")

    assert run("first", "second", "/q") is True
    assert "ProviderError: server exploded" in errors[0]
    assert shown == ["Recovered."]


def test_rate_limit_from_any_provider_offers_a_model_change(chat, fake_llm):
    run, shown, errors = chat
    fake_llm.failures.append(ProviderError(429))
    fake_llm.replies.append("From the new model.")

    assert run("first", "other-model", "second", "/q") is True
    assert fake_llm.calls[-1][1] == "other-model"
    assert shown == ["From the new model."]


def test_declining_a_model_change_keeps_the_session_open(chat, fake_llm):
    run, shown, errors = chat
    fake_llm.failures.append(ProviderError(429))
    fake_llm.replies.append("Worth the wait.")

    assert run("first", "second", "/q", confirm=False) is True
    assert shown == ["Worth the wait."]


def test_a_failed_model_change_keeps_the_current_model(chat, fake_llm, monkeypatch):
    run, shown, errors = chat
    statuses = []
    monkeypatch.setattr(
        default_ui,
        "status_message",
        lambda title, message, **k: statuses.append(message),
    )
    fake_llm.unavailable.add("broken-model")
    fake_llm.replies.append("Still here.")

    assert run("/model change broken-model", "/model", "hello", "/q") is True
    assert "Unknown model broken-model" in errors[0]
    assert statuses[-1] == "gpt-test"
    assert len(fake_llm.models) == 1
    assert shown == ["Still here."]


def test_a_missing_model_reverts_to_the_previous_one(chat, fake_llm):
    run, shown, errors = chat
    fake_llm.failures.append(ProviderError(404))
    fake_llm.replies.append("Back on the old model.")

    assert run("/model change gpt-typo", "first", "second", "/q") is True
    assert [call[1] for call in fake_llm.calls[-2:]] == ["gpt-typo", "gpt-test"]
    assert shown == ["Back on the old model."]
