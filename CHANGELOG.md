# Changelog

Notable changes to Ally are listed here, newest first. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 0.8.0 (unreleased)

A maintenance release. Ally now installs as a regular command line tool, starts about twice as fast, streams its replies and fixes a long list of bugs, several of which made RAG and non-OpenAI providers unreliable.

### Upgrading from 0.7

1. **Remove the old launcher.** Version 0.7 linked `ally` into your system rather than installing it.
   - Linux and macOS: `sudo rm /usr/local/bin/ally`
   - Windows: remove the Ally folder from your user `Path` environment variable, then delete `ally.bat` from that folder.
2. **Reinstall.** Pull the latest code and run `./setup.sh` or `.\setup.ps1` again. If you use Hugging Face embeddings (`"embedding_provider": "hf"`), add `--hf` or `-HF`, since PyTorch is now optional.
3. **Rebuild your RAG collections** with `/delete <collection>` and `/embed <path> <collection>`. Version 0.7 stored 50-character chunks, which retrieve poorly.
4. **Check your keys.** Each agent now uses only its own provider's API key. In 0.7, a missing key could be silently replaced by another provider's key. Ally now lists any missing keys when it starts.
5. **Clean up `.env`.** `GOOGLE_SEARCH_API_KEY`, `SEARCH_ENGINE_ID` and `GITHUB_AI_API_KEY` are no longer used. If `config.json` uses the `github` provider, switch to another one.

Python 3.11 or newer is required. The setup script installs it for you if needed.

### Added

- Replies stream into the terminal as they are generated, with a spinner until the first token.
- Web search works without an API key, using the [ddgs](https://pypi.org/project/ddgs/) metasearch library. Results include their URLs so answers can cite sources.
- `ally --version`, and long forms of every flag: `--dir`, `--prompt` and `--id`.
- `ALLY_CONFIG` selects a config file other than `config.json`.
- Ally reads messages from a pipe, one per line, for scripted use.
- `--dir` creates the working directory if it does not exist.
- Configuration errors, such as an unknown provider or a missing key, are all reported together at startup.
- Documentation in [`docs/`](docs), plus a security policy, contributing guide, code of conduct and issue templates.
- A test suite that runs without API keys, and CI on Linux and Windows.

### Changed

- The setup scripts install Ally with `uv tool install`, so `ally` works in any new terminal without changing system folders.
- Hugging Face embeddings are an optional extra (`hf`). Installs without it are several gigabytes smaller.
- Startup takes about 2.5 seconds instead of 5.6, and `ally --help` and `ally --version` return almost immediately.
- All dependencies are updated, including LangChain 1.7, LangGraph 1.2, the OpenAI SDK 3, Rich 15 and Transformers 5. Python 3.14 is supported.
- `pyproject.toml` and `uv.lock` define the dependencies, and the Docker image is built from the lockfile with CPU-only PyTorch.
- Tool descriptions are rewritten, and every tool argument is now described to the model.
- `list_directory` no longer expands `.git`, `node_modules` and virtual environments, which could flood the model's context.
- The four agents are built from one registry instead of four copies of the same code.

### Fixed

- Tools resolved relative paths against the folder Ally was started from instead of the working directory.
- `--dir ..` and other paths containing `.` or `..` were rejected on Windows.
- Replies from Anthropic and Gemini models, which arrive as lists of content blocks, crashed the display.
- Any provider error ended the chat session. Errors are now shown and the session continues.
- Rate limits and unknown models were only recognized for OpenAI. They are now recognized for every provider, and a misspelled model name switches back to the previous model.
- Declining a different model after a rate limit ended the session.
- `/model change` dropped the web search tool, lowercased the model name and could not undo a failed switch.
- Custom system prompts from `config.json` were ignored.
- When the approval prompt could not be shown, tools could run without approval. They are now denied.
- Commands typed after `!` lost their quotes.
- RAG skipped files that had changed since they were embedded, slept five seconds between batches, embedded the query once per collection, and could not use OpenAI embeddings at all.
- Search tools skipped any folder whose name started with an ignored name, such as `login/` because of `log`. They also searched `.env` files, which are now left out of search and RAG.
- The project workflow carried on to code generation after the brainstorming step failed.
- Logging a warning with exception details crashed, including in the chat loop's recursion limit handler.
- `setup.sh` was not executable after cloning.

### Removed

- The GitHub Models provider. GitHub retired the service in July 2026.
- Google Custom Search. Google closed the API to new customers and shuts it down on January 1, 2027.
- `requirements.txt`, replaced by `pyproject.toml` and `uv.lock`.

## 0.7.42 and earlier

See the [releases page](https://github.com/YassWorks/Ally/releases) for older versions.
