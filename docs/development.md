# Development

This page covers working on Ally itself: the setup, how the tests are built, how to try a change against a real model, and how releases are made. [CONTRIBUTING.md](../CONTRIBUTING.md) covers the pull request process and code style, and [Architecture](architecture.md) explains how the code fits together.

- [Setup](#setup)
- [Tests](#tests)
- [Trying a change for real](#trying-a-change-for-real)
- [Linting and formatting](#linting-and-formatting)
- [Continuous integration](#continuous-integration)
- [Dependencies](#dependencies)
- [Releasing](#releasing)

## Setup

```bash
git clone https://github.com/YassWorks/Ally.git
cd Ally
uv sync
```

`uv sync` creates `.venv` with Ally installed in editable mode and the development tools (pytest and Ruff). Add `--extra hf` to work on Hugging Face embeddings. Supported Python versions are 3.11 to 3.14.

Run your working copy with:

```bash
uv run ally
```

If you installed Ally with the setup script as well, both point at the same folder, so `ally` also runs your working copy.

## Tests

```bash
uv run pytest
```

The suite runs in a few seconds and needs no API keys or network access. It never calls a real model: `tests/conftest.py` replaces `create_chat_model` with `FakeProvider`, which hands out `FakeChatModel` instances that replay scripted replies.

| Fixture | What it gives you |
| --- | --- |
| `fake_llm` | The `FakeProvider`. Queue replies with `fake_llm.replies`, provider errors with `fake_llm.failures`, and make model names fail to load with `fake_llm.unavailable`. Inspect `fake_llm.calls` and each model's `received` messages. |
| `settings` | `AgentSettings` for a fake OpenAI model. |
| `isolated_history` | Applied to every test. Points the session database at a temporary folder. |

A reply can be plain text or an `AIMessage` with tool calls, so a test can drive a full tool loop:

```python
from langchain_core.messages import AIMessage

from app.src.core.agent_factory import AgentFactory
from app.src.core.permissions import permission_manager


def test_the_model_can_read_a_file(fake_llm, settings, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(permission_manager, "always_allow", True)
    (tmp_path / "notes.txt").write_text("pineapple", encoding="utf-8")
    fake_llm.replies.extend(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "read_file", "args": {"file_path": "notes.txt"}, "id": "1"}
                ],
            ),
            "The word is pineapple.",
        ]
    )

    agent = AgentFactory.create_agent("general", settings)
    answer = agent.invoke(message="Which word is in notes.txt?", quiet=True)

    assert answer == "The word is pineapple."
    assert fake_llm.last.received[-1][-1].content == "pineapple"
```

The existing tests are good starting points: `test_chat_loop.py` for the chat loop and error recovery, `test_streaming.py` for the live view, `test_cli.py` for a whole session and `test_project_workflow.py` for the project workflow.

Tools that ask for approval check `permission_manager.always_allow`, as above. Always patch it with `monkeypatch` so the change does not leak into other tests.

## Trying a change for real

Unit tests do not catch everything a real model does. To try a change against a provider without touching your own sessions or knowledge base, give Ally a throwaway config and data folders:

```bash
mkdir -p /tmp/ally-try
echo '{"provider": "ollama", "model": "qwen3"}' > /tmp/ally-try/config.json
export ALLY_CONFIG=/tmp/ally-try/config.json
export ALLY_HISTORY_DIR=/tmp/ally-try/history
export ALLY_DATABASE_DIR=/tmp/ally-try/db
uv run ally --dir /tmp/ally-try
```

Piping input makes a run repeatable, which is handy when comparing behavior before and after a change:

```bash
printf 'Create notes.txt containing hello\n/q\n' | uv run ally --dir /tmp/ally-try --allow-all-tools
```

Free tiers of hosted providers rate limit quickly. A local Ollama model avoids that, but small models use tools less reliably, so try a strong hosted model before concluding that something is broken.

## Linting and formatting

[Ruff](https://docs.astral.sh/ruff/) handles both. The rules are in `pyproject.toml`.

```bash
uv run ruff check .
uv run ruff format .
```

`ruff check --fix` applies the safe automatic fixes.

## Continuous integration

GitHub Actions runs two workflows:

- **CI** (`.github/workflows/ci.yml`) on every pull request and every push to `main`: Ruff, then the tests on Ubuntu with Python 3.11 and 3.13 and on Windows with Python 3.13. All four checks must pass before a pull request can be merged.
- **Docker** (`.github/workflows/docker-publish.yml`) builds the image and checks that `ally --version` runs in it. It runs on pull requests that touch the Dockerfile or the dependencies, and publishes the image when a release is published.

`main` keeps a linear history: pull requests are squash merged.

## Dependencies

Dependencies are pinned to exact versions in `pyproject.toml`, and `uv.lock` pins everything else. To upgrade one:

```bash
uv add "rich==15.0.0"
```

`uv add` updates both files. Commit them together, and run the tests on every supported operating system when the upgrade is large.

PyTorch is only needed for Hugging Face embeddings, so it lives in the optional `hf` extra. On Linux it comes from PyTorch's CPU-only index, configured under `[tool.uv.sources]`, which keeps the install and the Docker image several gigabytes smaller than the default CUDA build.

## Releasing

1. Update `version` in `pyproject.toml` and move the "Unreleased" notes in `CHANGELOG.md` under the new version.
2. Merge that change to `main`.
3. Publish a GitHub release whose tag is the version, for example `0.8.0`.

Publishing the release builds the Docker image and pushes it to Docker Hub as `yassw0rks/ally:<version>` and `yassw0rks/ally:latest`. This needs the `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` repository secrets.
