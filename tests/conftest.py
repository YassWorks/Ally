from collections.abc import Iterator
from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from pydantic import Field

from app.config import AgentSettings
from app.src.core import create_base_agent


class FakeChatModel(GenericFakeChatModel):
    """Chat model that replays scripted replies and records what it was sent."""

    received: list = Field(default_factory=list)
    bound_tools: list = Field(default_factory=list)
    provider: Any = None

    def bind_tools(self, tools, **kwargs):
        self.bound_tools[:] = [tool.name for tool in tools]
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.received.append(messages)
        if self.provider is not None and self.provider.failures:
            raise self.provider.failures.pop(0)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


class FakeProvider:
    """Stands in for ``create_chat_model`` and hands out fake models."""

    def __init__(self):
        self.replies: list[AIMessage | str] = []
        self.failures: list[Exception] = []
        self.models: list[FakeChatModel] = []
        self.calls: list[tuple] = []

    def __call__(self, provider, model_name, api_key, temperature=None):
        self.calls.append((provider, model_name, api_key, temperature))
        model = FakeChatModel(messages=self._replies(), provider=self)
        self.models.append(model)
        return model

    def _replies(self) -> Iterator[AIMessage | str]:
        while self.replies:
            yield self.replies.pop(0)

    @property
    def last(self) -> FakeChatModel:
        return self.models[-1]


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setenv("ALLY_HISTORY_DIR", str(tmp_path / "history"))
    monkeypatch.setattr(create_base_agent, "_checkpointer", None)


@pytest.fixture
def fake_llm(monkeypatch) -> FakeProvider:
    fake = FakeProvider()
    monkeypatch.setattr(create_base_agent, "create_chat_model", fake)
    return fake


@pytest.fixture
def settings() -> AgentSettings:
    return AgentSettings(provider="openai", model="gpt-test", api_key="sk-test")
