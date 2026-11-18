import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

AGENT_TYPES = ("general", "code_gen", "brainstormer", "web_searcher")

PROVIDER_KEY_ENV: dict[str, str | None] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_GEN_AI_API_KEY",
    "groq": "GROQ_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "github": "GITHUB_AI_API_KEY",
    "ollama": None,
}


class ConfigError(Exception):
    """Raised when ``config.json`` or the API keys it relies on are missing or invalid."""


@dataclass(frozen=True)
class AgentSettings:
    """Everything needed to build one agent's chat model."""

    provider: str
    model: str
    api_key: str | None = None
    temperature: float | None = None
    system_prompt: str | None = None


@dataclass(frozen=True)
class AllyConfig:
    """Resolved configuration for a whole Ally session."""

    agents: dict[str, AgentSettings]
    embedding_provider: str = ""
    embedding_model: str = ""
    scraping_method: str = "simple"


def load_config(path: Path, env: Mapping[str, str] | None = None) -> AllyConfig:
    """Read ``config.json`` from ``path`` and resolve it against ``env``.

    Raises:
        ConfigError: If the file is missing, is not valid JSON, or describes an unusable setup.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {path}") from None
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"{path.name} is not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}"
        ) from None

    if not isinstance(raw, dict):
        raise ConfigError(f"{path.name} must contain a JSON object.")

    return resolve_config(raw, os.environ if env is None else env)


def resolve_config(raw: Mapping, env: Mapping[str, str]) -> AllyConfig:
    """Turn raw ``config.json`` values into per-agent settings.

    Per-agent ``provider_per_model`` and ``models`` entries fall back to the top-level
    ``provider`` and ``model``. Each agent gets the API key of its own provider, and every
    problem found is reported at once.

    Raises:
        ConfigError: If a provider is unknown, a model is missing, or an API key is not set.
    """
    default_provider = _normalize(raw.get("provider"))
    default_model = raw.get("model")
    providers = raw.get("provider_per_model") or {}
    models = raw.get("models") or {}
    temperatures = raw.get("temperatures") or {}
    system_prompts = raw.get("system_prompts") or {}

    agents: dict[str, AgentSettings] = {}
    problems: list[str] = []
    missing_keys: dict[str, list[str]] = {}

    for name in AGENT_TYPES:
        provider = _normalize(providers.get(name)) or default_provider
        model = models.get(name) or default_model

        if not provider:
            problems.append(
                f'No provider set for "{name}". Set "provider" in config.json.'
            )
            continue
        if provider not in PROVIDER_KEY_ENV:
            supported = ", ".join(PROVIDER_KEY_ENV)
            problems.append(
                f'Unknown provider "{provider}" for "{name}". Use one of: {supported}.'
            )
            continue
        if not model:
            problems.append(
                f'No model set for "{name}". Set "model" or "models.{name}".'
            )

        key_env = PROVIDER_KEY_ENV[provider]
        api_key = env.get(key_env) if key_env else None
        if key_env and not api_key:
            missing_keys.setdefault(key_env, []).append(name)

        agents[name] = AgentSettings(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=temperatures.get(name),
            system_prompt=system_prompts.get(name) or None,
        )

    for key_env, names in missing_keys.items():
        problems.append(f"{key_env} is not set. It is needed by: {', '.join(names)}.")

    if problems:
        raise ConfigError("Invalid configuration:\n- " + "\n- ".join(problems))

    return AllyConfig(
        agents=agents,
        embedding_provider=_normalize(raw.get("embedding_provider")),
        embedding_model=raw.get("embedding_model") or "",
        scraping_method=raw.get("scraping_method") or "simple",
    )


def _normalize(value: object) -> str:
    return str(value).strip().lower() if value else ""
