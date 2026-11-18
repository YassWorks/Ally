import pytest

from app.config import AgentSettings
from app.src.core.agent_factory import CODING_AGENTS, AgentFactory
from app.src.core.ui import default_ui
from app.src.orchestration.units.orchestrated_codegen import CodeGenUnit


class ServerError(Exception):
    status_code = 500


@pytest.fixture
def workflow(fake_llm, monkeypatch, tmp_path):
    settings = {
        name: AgentSettings(provider="openai", model=name, api_key="sk-test")
        for name in CODING_AGENTS
    }
    agents = AgentFactory.create_coding_agents(settings)
    unit = CodeGenUnit(
        code_gen_agent=agents["code_gen"],
        web_searcher_agent=agents["web_searcher"],
        brainstormer_agent=agents["brainstormer"],
    )
    errors = []
    for name in ("status_message", "ai_response", "goodbye", "tool_call"):
        monkeypatch.setattr(default_ui, name, lambda *a, **k: None)
    monkeypatch.setattr(default_ui, "error", errors.append)
    monkeypatch.setattr(default_ui, "confirm", lambda *a, **k: False)
    monkeypatch.setattr(default_ui, "get_input", lambda *a, **k: "/q")

    def run():
        return unit.run(
            prompt="a tiny date script",
            working_dir=str(tmp_path),
            stream=False,
            show_welcome=False,
        )

    return run, errors


def asked(fake_llm, model):
    return sum(
        len(created.received)
        for call, created in zip(fake_llm.calls, fake_llm.models, strict=True)
        if call[1] == model
    )


def test_workflow_runs_every_phase(workflow, fake_llm):
    run, errors = workflow
    fake_llm.replies.extend(["Context files written.", "Code written."])

    assert run() is True
    assert asked(fake_llm, "brainstormer") == 1
    assert asked(fake_llm, "code_gen") == 1
    assert errors == []


def test_workflow_stops_when_brainstorming_fails(workflow, fake_llm):
    run, errors = workflow
    fake_llm.failures.append(ServerError("boom"))

    assert run() is False
    assert asked(fake_llm, "code_gen") == 0
    assert len(errors) == 1
