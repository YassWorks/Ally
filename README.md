<div align="center">

<img src="assets/ally_cover.png" alt="Ally" width="80%" />

[![CI](https://github.com/YassWorks/Ally/actions/workflows/ci.yml/badge.svg)](https://github.com/YassWorks/Ally/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/YassWorks/Ally)](https://github.com/YassWorks/Ally/releases)
[![Python](https://img.shields.io/badge/python-3.11%20to%203.14-3776ab)](pyproject.toml)
[![License](https://img.shields.io/github/license/YassWorks/Ally)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/YassWorks/Ally?style=social)](https://github.com/YassWorks/Ally/stargazers)

**A private, provider-agnostic AI agent for your terminal.**

</div>

Ally is a command line agent that chats with you, reads and edits your files, runs commands, searches the web and answers questions from your own documents. It can run entirely on your machine with [Ollama](https://ollama.com), or use OpenAI, Anthropic, Google Gemini, Groq, Cerebras or OpenRouter, and you can mix providers across its agents.

## Highlights

- **Tools that ask first.** File, shell, Python, git, code search and web tools. Every call is shown and needs your approval unless you allow it.
- **Local RAG.** Embed folders of text, Markdown, PDF and DOCX files into a local Chroma database and chat with them, with references to the files used.
- **Any model, per agent.** Choose a provider and model for each agent in one config file, and switch models mid-chat with `/model change`.
- **Live replies.** Answers stream into the terminal as they are generated and are rendered as Markdown.
- **Sessions you can resume.** Every conversation is saved locally under an ID you can come back to.
- **Project generation (preview).** A brainstorming agent writes a project specification, then a coding agent builds it with you.

## Quick start

You need [Git](https://git-scm.com/downloads) and [uv](https://docs.astral.sh/uv/getting-started/installation/). uv installs a suitable Python for you.

```bash
git clone https://github.com/YassWorks/Ally.git
cd Ally
cp .env.example .env
./setup.sh
```

On Windows, run the same steps in PowerShell with `copy .env.example .env` and `.\setup.ps1`.

Put the API key for your provider in `.env`, then set the provider and model in `config.json`:

```json
{
    "provider": "google",
    "model": "gemini-3-flash-preview"
}
```

Open a new terminal and start chatting:

```bash
ally
```

For a fully local setup, install [Ollama](https://ollama.com/download), pull a model and use `"provider": "ollama"`. No API key is needed. To run Ally in Docker instead, see [Getting started](docs/getting-started.md#docker).

## Usage

```text
ally [--dir DIR] [--prompt PROMPT] [--id ID] [--allow-all-tools] [--create-project] [--version]
```

| Flag | What it does |
| --- | --- |
| `-d`, `--dir` | Work in this directory. It is created if it does not exist. |
| `-p`, `--prompt` | Send this message first. |
| `-i`, `--id` | Resume the session with this ID. |
| `--allow-all-tools` | Run tools without asking. Use with care. |
| `--create-project` | Start the project generation workflow. |
| `--version` | Print the version and exit. |

Inside a chat, type `/help` for every command. The most useful ones:

| Command | What it does |
| --- | --- |
| `!<command>` | Run a shell command yourself, without involving the model. |
| `/model`, `/model change <name>` | Show or switch the model. |
| `/id`, `/id <id>` | Show the session ID, or switch to another session. |
| `/clear` | Start a fresh conversation. |
| `/embed <path> <collection>` | Add files to the knowledge base. |
| `/start_rag`, `/stop_rag` | Answer from the knowledge base, or stop doing so. |
| `/project` | Start the project generation workflow. |
| `/q` | Quit. |

Ally also reads from a pipe, one message per line, which is handy for scripts:

```bash
echo "Summarize README.md in three bullet points" | ally --dir . --allow-all-tools
```

## Documentation

- [Getting started](docs/getting-started.md): installation, Docker, first steps and updating.
- [Configuration](docs/configuration.md): `config.json`, API keys, environment variables and where data is stored.
- [Tools and permissions](docs/tools-and-permissions.md): what each tool does and how approval works.
- [RAG](docs/rag.md): building a knowledge base from your files and chatting with it.
- [Architecture](docs/architecture.md): how the agents, tools and storage fit together.
- [Development](docs/development.md): running the tests, the code layout and releasing.

## Contributing

Issues and pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first, and report security problems as described in [SECURITY.md](SECURITY.md). Changes between versions are listed in the [changelog](CHANGELOG.md).

## License

Ally is released under the [Apache 2.0 license](LICENSE).
