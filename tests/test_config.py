import json

import pytest

from app.config import AGENT_TYPES, ConfigError, load_config, resolve_config

BASE = {"provider": "openai", "model": "gpt-test"}


def test_per_agent_settings_fall_back_to_defaults():
    config = resolve_config(BASE, {"OPENAI_API_KEY": "sk-openai"})

    for name in AGENT_TYPES:
        agent = config.agents[name]
        assert (agent.provider, agent.model, agent.api_key) == (
            "openai",
            "gpt-test",
            "sk-openai",
        )


def test_each_agent_gets_its_own_providers_key():
    raw = {
        **BASE,
        "provider_per_model": {"code_gen": "anthropic"},
        "models": {"code_gen": "claude-test"},
    }
    env = {"OPENAI_API_KEY": "sk-openai", "ANTHROPIC_API_KEY": "sk-anthropic"}

    config = resolve_config(raw, env)

    assert config.agents["code_gen"].api_key == "sk-anthropic"
    assert config.agents["general"].api_key == "sk-openai"


def test_missing_key_is_reported_instead_of_borrowing_another_providers_key():
    raw = {**BASE, "provider_per_model": {"code_gen": "anthropic"}}

    with pytest.raises(
        ConfigError, match="ANTHROPIC_API_KEY is not set. It is needed by: code_gen"
    ):
        resolve_config(raw, {"OPENAI_API_KEY": "sk-openai"})


def test_ollama_needs_no_key():
    config = resolve_config({"provider": "ollama", "model": "qwen3"}, {})

    assert config.agents["general"].api_key is None


def test_unknown_provider_and_missing_model_are_reported_together():
    raw = {"provider": "nope", "provider_per_model": {"general": "openai"}}

    with pytest.raises(ConfigError) as error:
        resolve_config(raw, {"OPENAI_API_KEY": "sk"})

    assert 'Unknown provider "nope"' in str(error.value)
    assert 'No model set for "general"' in str(error.value)


def test_temperature_and_prompts_are_optional():
    raw = {**BASE, "temperatures": {"general": 0}, "system_prompts": {"general": ""}}

    config = resolve_config(raw, {"OPENAI_API_KEY": "sk"})

    assert config.agents["general"].temperature == 0
    assert config.agents["code_gen"].temperature is None
    assert config.agents["general"].system_prompt is None


def test_load_config_reports_invalid_json(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{ not json", encoding="utf-8")

    with pytest.raises(ConfigError, match="not valid JSON"):
        load_config(path, {})


def test_load_config_reports_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "missing.json", {})


def test_load_config_reads_embedding_settings(tmp_path):
    path = tmp_path / "config.json"
    raw = {**BASE, "embedding_provider": "Ollama", "embedding_model": "all-minilm"}
    path.write_text(json.dumps(raw), encoding="utf-8")

    config = load_config(path, {"OPENAI_API_KEY": "sk"})

    assert (config.embedding_provider, config.embedding_model) == (
        "ollama",
        "all-minilm",
    )
