from dataclasses import replace

import pytest
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

from app.src.agents.registry import AGENT_SPECS, default_system_prompt
from app.src.core.agent_factory import AgentFactory


@tool
def extra_tool(text: str) -> str:
    """Echo ``text``."""
    return text


def test_every_agent_type_builds(fake_llm, settings):
    for name, spec in AGENT_SPECS.items():
        agent = AgentFactory.create_agent(name, settings)

        assert fake_llm.last.bound_tools == [t.name for t in spec.tools]
        assert agent.model_name == "gpt-test"


def test_unknown_agent_type(settings):
    with pytest.raises(ValueError):
        AgentFactory.create_agent("nope", settings)


def test_default_prompt_has_date_filled_in():
    prompt = default_system_prompt(AGENT_SPECS["general"])

    assert "{date}" not in prompt


def test_model_change_keeps_extra_tools_and_case(fake_llm, settings):
    agent = AgentFactory.create_agent("general", settings)
    agent.add_tools([extra_tool])

    agent._handle_model_command("/model change Meta-Llama/Llama-3.3-70B-Instruct")

    assert agent.model_name == "Meta-Llama/Llama-3.3-70B-Instruct"
    assert fake_llm.calls[-1][1] == "Meta-Llama/Llama-3.3-70B-Instruct"
    assert "extra_tool" in fake_llm.last.bound_tools


def test_model_change_reverts_when_the_new_model_fails(fake_llm, settings, monkeypatch):
    agent = AgentFactory.create_agent("general", settings)

    def broken(*args, **kwargs):
        raise RuntimeError("model not found")

    monkeypatch.setattr("app.src.core.create_base_agent.create_chat_model", broken)

    with pytest.raises(RuntimeError):
        agent._handle_model_change("missing-model")

    assert agent.model_name == "gpt-test"


def test_custom_system_prompt_survives_adding_tools(fake_llm, settings):
    custom = replace(settings, system_prompt="You are a pirate {not a template}.")
    agent = AgentFactory.create_agent("general", custom)
    agent.add_tools([extra_tool])
    fake_llm.replies.append("Arr.")

    reply = agent.invoke("hello")

    system = fake_llm.last.received[-1][0]
    assert isinstance(system, SystemMessage)
    assert system.content == "You are a pirate {not a template}."
    assert reply == "Arr."
