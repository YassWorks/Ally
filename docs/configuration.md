# Configuration

Ally has two kinds of settings: `config.json` chooses models and features, and environment variables hold API keys and override where data is stored.

- [config.json](#configjson)
- [Agents](#agents)
- [Settings reference](#settings-reference)
- [API keys and environment variables](#api-keys-and-environment-variables)
- [Web search](#web-search)
- [Where Ally keeps its data](#where-ally-keeps-its-data)

## config.json

Ally reads `config.json` from the folder you cloned it into. To keep several configurations, or to keep yours outside the repository, point `ALLY_CONFIG` at another file:

```bash
ALLY_CONFIG=~/.config/ally/work.json ally
```

Only `provider` and `model` are required. Everything else falls back to sensible defaults.

```json
{
    "provider": "google",
    "model": "gemini-3-flash-preview"
}
```

A fuller example that runs the main chat locally, sends coding work to a hosted model and enables RAG with local embeddings:

```json
{
    "provider": "ollama",
    "model": "qwen3",

    "provider_per_model": {
        "code_gen": "anthropic"
    },
    "models": {
        "code_gen": "claude-sonnet-5-5"
    },

    "temperatures": {
        "general": 0.7
    },

    "embedding_provider": "ollama",
    "embedding_model": "all-minilm"
}
```

Ally checks the whole file when it starts and lists every problem at once, so you can fix them in one go:

```text
Invalid configuration:
- Unknown provider "gemini" for "general". Use one of: openai, anthropic, google, groq, cerebras, openrouter, ollama.
- ANTHROPIC_API_KEY is not set. It is needed by: code_gen.
```

## Agents

Ally is made of four agents. Each one can use its own provider, model, temperature and system prompt.

| Agent | Key | What it does |
| --- | --- | --- |
| General | `general` | The main chat. Has the file, shell, Python, search and web tools. |
| Web searcher | `web_searcher` | Researches questions on the web when another agent asks it to. |
| Brainstormer | `brainstormer` | Writes the project specification in the [project workflow](#project-workflow). |
| Coding | `code_gen` | Builds the project from that specification. |

When a setting is missing or `null` for an agent, the agent uses the top-level `provider` and `model`.

### Project workflow

`ally --create-project`, or `/project` inside a chat, runs the brainstormer and then the coding agent. It first shows the models each one will use and lets you change them for that run. The workflow is a preview: it works best with strong models that handle long tool sequences well.

## Settings reference

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `provider` | string | required | Default provider for every agent. |
| `model` | string | required | Default model for every agent. |
| `provider_per_model` | object | `{}` | Provider per agent, keyed by agent. |
| `models` | object | `{}` | Model per agent, keyed by agent. |
| `temperatures` | object | `{}` | Sampling temperature per agent. When unset, the provider's default is used. |
| `system_prompts` | object | `{}` | Replaces an agent's built-in system prompt with your own text. |
| `embedding_provider` | string | none | `hf`, `ollama`, `openai` or `nlp_cloud`. Leave it unset to turn RAG off. |
| `embedding_model` | string | per provider | Embedding model to use. See [RAG](rag.md#embedding-providers) for the defaults. |
| `scraping_method` | string | `simple` | How files are read for RAG. `simple` is the only method today. |

Provider names are case-insensitive. Valid providers are `openai`, `anthropic`, `google`, `groq`, `cerebras`, `openrouter` and `ollama`.

The built-in system prompts live in [`app/prompts`](../app/prompts). A custom prompt replaces the built-in one entirely, so start from a copy of it if you only want to adjust it.

## API keys and environment variables

Ally loads `.env` from the folder you cloned it into. Variables already set in your shell take precedence over `.env`, so you can also export keys from your shell profile or a secrets manager.

| Variable | Used for |
| --- | --- |
| `OPENAI_API_KEY` | The `openai` provider, and OpenAI embeddings. |
| `ANTHROPIC_API_KEY` | The `anthropic` provider. |
| `GOOGLE_GEN_AI_API_KEY` | The `google` provider. |
| `GROQ_API_KEY` | The `groq` provider. |
| `CEREBRAS_API_KEY` | The `cerebras` provider. |
| `OPENROUTER_API_KEY` | The `openrouter` provider. |
| `NLP_CLOUD_API_KEY` | NLP Cloud embeddings. |
| `GOOGLE_SEARCH_API_KEY`, `SEARCH_ENGINE_ID` | Web search. See [below](#web-search). |
| `OLLAMA_HOST` | Address of the Ollama server, if it is not `http://localhost:11434`. |
| `ALLY_CONFIG` | Path to the config file to use instead of `config.json`. |
| `ALLY_HISTORY_DIR`, `ALLY_DATABASE_DIR`, `ALLY_EMBEDDING_MODELS_DIR` | Where Ally stores its data. See [below](#where-ally-keeps-its-data). |

Only the keys for the providers you actually use are needed.

## Web search

The web searcher uses Google's Custom Search JSON API. Without it, everything else still works and the search tool tells the model that search is not configured.

1. Create a search engine in the [Programmable Search Engine control panel](https://programmablesearchengine.google.com/controlpanel/all) and turn on **Search the entire web**. Copy its **Search engine ID**.
2. Create an API key for the [Custom Search JSON API](https://developers.google.com/custom-search/v1/overview) in the same Google Cloud project.
3. Add both to `.env`:

   ```text
   GOOGLE_SEARCH_API_KEY=your-api-key
   SEARCH_ENGINE_ID=your-search-engine-id
   ```

Fetching a page from a known URL does not need these keys.

## Where Ally keeps its data

Ally stores everything under one data directory:

- Windows: `%LOCALAPPDATA%\Ally`
- Linux and macOS: `~/.local/share/Ally`

| Folder | Contents | Override |
| --- | --- | --- |
| `history` | Every session, in a SQLite database. | `ALLY_HISTORY_DIR` |
| `database` | The RAG knowledge base (Chroma). | `ALLY_DATABASE_DIR` |
| `embedding_models` | Hugging Face models downloaded for embeddings. | `ALLY_EMBEDDING_MODELS_DIR` |
| `logs` | One log file per day, named `ally_YYYYMMDD.log`. | none |

Messages on screen are kept short. When something goes wrong, the full error and stack trace are in the log file, which is the first place to look and the most useful thing to attach to a bug report.

Deleting a folder resets that part of Ally: removing `history` forgets all sessions, and removing `database` empties the knowledge base.
