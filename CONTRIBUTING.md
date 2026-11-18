# Contributing to Ally

Thanks for taking the time to help. Bug reports, fixes, documentation and small features are all welcome. For anything larger, open an issue first so the approach can be agreed on before you spend time on it.

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md). Security problems are reported privately, as described in [SECURITY.md](SECURITY.md).

## Reporting a bug

Open an issue with the bug report form. The most useful reports include:

- `ally --version`, your operating system and the provider and model you used,
- what you did, what you expected and what happened instead,
- the matching lines from the log file. The [configuration guide](docs/configuration.md#where-ally-keeps-its-data) says where logs are kept. Remove anything private before pasting.

## Setting up

You need [Git](https://git-scm.com/downloads) and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/YassWorks/Ally.git
cd Ally
uv sync
uv run ally --version
```

`uv sync` creates `.venv` with Ally, its dependencies and the development tools. Add `--extra hf` if you work on Hugging Face embeddings, which pulls in PyTorch.

Run your working copy with `uv run ally`. It reads `config.json` and `.env` from the repository folder, or the config file named by `ALLY_CONFIG`.

## Making a change

1. Create a branch from `main`.
2. Make the change and add or update tests.
3. Run the same checks as CI:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest
   ```

4. Open a pull request that explains what changed and why.

The tests replace the chat model with a scripted fake, so they need no API keys or network access. [Development](docs/development.md) explains how they are put together and how to try a change against a real provider.

## Style

- Keep pull requests small and focused on one thing. Several small pull requests are easier to review than one large one.
- Use [Conventional Commits](https://www.conventionalcommits.org/) prefixes in commit messages and pull request titles, such as `fix:`, `feat:`, `docs:`, `refactor:`, `perf:`, `build:` or `ci:`.
- Ruff handles formatting and import order. Do not reformat code you are not changing.
- Prefer clear names and small functions over comments. The codebase has no comments, and new code should not add any.
- Public functions and classes get a Google style docstring: a one-line summary in the imperative mood, then `Args`, `Returns` or `Raises` sections only when they add something.
- Tool docstrings are sent to the model as the tool's description, so write them for the model: say what the tool does and when to use it, and describe every argument.
- Dependencies are pinned to exact versions in `pyproject.toml`. When you add or change one, run `uv lock` and commit `uv.lock` with it.

## Pull requests

CI runs the linter and the tests on Linux and Windows. A pull request is merged once CI passes and it has been reviewed. Pull requests are squash merged, so the title becomes the commit message on `main`.
