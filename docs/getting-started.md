# Getting started

This guide installs Ally, connects it to a model and walks through a first session. It takes about five minutes, most of it spent downloading dependencies.

- [Install](#install)
- [Choose a model](#choose-a-model)
- [Your first session](#your-first-session)
- [Docker](#docker)
- [Updating and uninstalling](#updating-and-uninstalling)

## Install

You need:

- [Git](https://git-scm.com/downloads), or a downloaded copy of this repository.
- [uv](https://docs.astral.sh/uv/getting-started/installation/). It also installs a suitable Python if you do not have Python 3.11 or newer.
- [Ollama](https://ollama.com/download), only if you want to run models locally.

Clone the repository and create your `.env` file from the template:

```bash
git clone https://github.com/YassWorks/Ally.git
cd Ally
cp .env.example .env
```

Then run the setup script for your system.

On Linux and macOS:

```bash
./setup.sh
```

On Windows, in PowerShell:

```powershell
copy .env.example .env
.\setup.ps1
```

The script installs Ally as a [uv tool](https://docs.astral.sh/uv/concepts/tools/), in its own environment, and adds the `ally` command to your `PATH`. Open a new terminal and check that it works:

```bash
ally --version
```

The install is editable: Ally keeps reading `config.json`, `.env` and its code from the folder you cloned, so edits there take effect the next time you start it. Keep the folder where it is.

### Optional: local Hugging Face embeddings

To build a knowledge base with Hugging Face models running on your machine, install the `hf` extra. It adds PyTorch and Transformers, which is a large download.

```bash
./setup.sh --hf
```

```powershell
.\setup.ps1 -HF
```

The other embedding providers (Ollama, OpenAI and NLP Cloud) do not need it. See [RAG](rag.md).

## Choose a model

Ally reads its settings from `config.json` in the folder you cloned. The smallest useful config names a provider and a model:

```json
{
    "provider": "ollama",
    "model": "qwen3"
}
```

Supported providers and the key each one needs in `.env`:

| Provider | `"provider"` | Key in `.env` | Example model |
| --- | --- | --- | --- |
| Ollama (local) | `ollama` | none | `qwen3` |
| OpenAI | `openai` | `OPENAI_API_KEY` | `gpt-5.4` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | `claude-sonnet-5-5` |
| Google Gemini | `google` | `GOOGLE_GEN_AI_API_KEY` | `gemini-3-flash-preview` |
| Groq | `groq` | `GROQ_API_KEY` | `openai/gpt-oss-120b` |
| Cerebras | `cerebras` | `CEREBRAS_API_KEY` | `gpt-oss-120b` |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` | `openai/gpt-4.1-mini` |

Model names change often. Use the exact name from your provider's model list. For Ollama, pull the model first:

```bash
ollama pull qwen3
```

Ally works best with models that support tool calling. Small local models may skip tools or misuse them.

To let Ally search the web, add a Google Programmable Search Engine key and engine ID to `.env`. The [configuration guide](configuration.md#web-search) explains how to get them. Everything else works without them.

[Configuration](configuration.md) covers every setting, including using a different provider or model for each agent.

## Your first session

Start Ally in the folder you want to work in:

```bash
ally --dir ~/projects/demo
```

Without `--dir`, Ally shows the current directory and asks whether you want to change it. Tools work inside this directory, and relative paths are resolved against it.

Type a request and press Enter. Use `Ctrl+N` for a new line.

```text
> Create a hello.py that prints the current date, then run it
```

When the model wants to use a tool, Ally shows the call and asks before running it:

```text
> create_file
file_path:
hello.py
content:
from datetime import date...

Attempting to call 'create_file'

   >  1. Yes, allow once
      2. No, deny access (request modifications)
      3. Yes, always allow this tool (create_file) to run
      4. Yes, always allow all tools to run freely (USE AT YOUR OWN RISK)
```

If you deny a call, the model is told and can try something else or ask you what to change. [Tools and permissions](tools-and-permissions.md) explains each tool and answer.

A few things worth knowing early:

- `!` runs a shell command yourself, for example `!git status`. The model is not involved.
- `/help` lists every command.
- `/model change <name>` switches the model without losing the conversation.
- `/q` quits.

### Resuming a session

Every conversation is saved under a session ID. Show it with `/id`, then resume it later:

```bash
ally --id 3f0c9a6e-1b2d-4c51-9e7a-0d4b8f2a6c13
```

You can also switch sessions from inside a chat with `/id <id>`, or start over with `/clear`.

### Non-interactive use

Ally reads messages from a pipe, one per line, and exits when the input ends. Tool calls cannot be approved without a terminal, so add `--allow-all-tools` if the task needs tools:

```bash
echo "List the Python files here and summarize what each one does" | ally --dir . --allow-all-tools
```

`--prompt` sends a first message and then stays in the interactive chat:

```bash
ally --dir . --prompt "Explain the structure of this project"
```

## Docker

The image on Docker Hub contains Ally with every optional dependency, plus `git` and `nano`. It does not contain Ollama.

Put your keys in a `.env` file, then start a container:

```bash
docker run -it --env-file .env --name ally yassw0rks/ally:latest
```

The container opens a shell. Edit `/app/config.json` with `nano`, then run `ally`.

To work on files from your machine, mount a folder and point Ally at it. A named volume for Ally's data keeps your sessions, knowledge base and downloaded embedding models when the container is replaced:

```bash
docker run -it \
  --env-file .env \
  -v "$(pwd)":/data \
  -v ally-data:/root/.local/share/Ally \
  --name ally \
  yassw0rks/ally:latest
```

```bash
ally --dir /data
```

To use Ollama running on your machine from inside the container, add `-e OLLAMA_HOST=http://host.docker.internal:11434` to `docker run`. On Linux, also add `--add-host=host.docker.internal:host-gateway`.

To come back to the same container later:

```bash
docker start -ai ally
```

## Updating and uninstalling

To update, pull the latest code and run the setup script again so new dependencies are installed:

```bash
git pull
./setup.sh
```

Check the [changelog](../CHANGELOG.md) for anything that needs your attention, such as settings that changed.

To uninstall, remove the tool, then delete the cloned folder and, if you want, Ally's data directory (see [where Ally keeps its data](configuration.md#where-ally-keeps-its-data)):

```bash
uv tool uninstall ally
```
