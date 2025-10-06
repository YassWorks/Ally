# Ally

<div align="center">

<img src="https://private-user-images.githubusercontent.com/166346524/497934948-e743b381-29af-4bbb-b98a-e08e3f275684.jpg?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTk3NzM0MDksIm5iZiI6MTc1OTc3MzEwOSwicGF0aCI6Ii8xNjYzNDY1MjQvNDk3OTM0OTQ4LWU3NDNiMzgxLTI5YWYtNGJiYi1iOThhLWUwOGUzZjI3NTY4NC5qcGc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMDA2JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTAwNlQxNzUxNDlaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1mYWY4MjJiNzY5ZTUyYWQ1NDhiNjE5MzkxYzMyNzk3N2Q3NDhmOGExZDc3ZmY5ZDMzODUwYTY2OWZkYzE1OTMyJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.f5dDsMzeCdIJ9ZIQDatsdRwkc1BeS8DTg_xwjZ2XQbM">

<p align="center">
  <a href="https://github.com/YassWorks/Ally/stargazers">
    <img src="https://img.shields.io/github/stars/YassWorks/Ally?style=flat-square&color=brightgreen" alt="GitHub stars">
  </a>
  <a href="https://github.com/YassWorks/Ally/network/members">
    <img src="https://img.shields.io/github/forks/YassWorks/Ally?style=flat-square&color=blue" alt="GitHub forks">
  </a>
</p>

</div>

Ally is an AI-powered CLI tool designed to assist with anything from everyday tasks to complex projects efficiently, without leaving the terminal.

Ally was built a fully local agentic system using **[Ollama](https://ollama.com/download)**, but it also works seamlessly with:

* OpenAI
* Anthropic
* Google GenAI
* Cerebras
* *(more integrations on the way!)*

This tool is best suited for scenarios where privacy is paramount and agentic capabilities are needed in the workflow.

## Key Features

### Default Chat Interface

A general-purpose agent that can:

* Read, write, modify, and delete files and directories.
* Access the internet.
* Execute commands and code.

  ***Note:*** Tools always ask for your permission before executing.

### RAG

Ally can take your files, embed them into its knowledge base, and use them to respond to your prompts with a high level of accuracy.

Currently, Ally's embedding functions can use:

- Hugging Face models (locally)
- Ollama Embedding models (locally)
- More on the way.

**RAG Tutorial:**

1. Setup the `config.json` as shown below with the appropriate embedding settings.

2. Provide the path to the file or folder whose contents should be embedded. As an alternative, you can launch Ally from that directory.

3. Use `/embed <path> <collection_name>` or `/embed . <collection_name>` if already at the correct path.

4. Start the RAG session with `/start_rag`

5. End the RAG session with `/stop_rag`

**Note** that Ally will not use any external data to answer your prompts during RAG sessions unless explicitly given permission to.

**Additional commands:**

- Edit indexed collections with `/index <collection_name>` and `/unindex <collection_name>.` ***Note:*** newly created collections are already indexed.

- View all collections with `/list`

- Reset the database with `/purge` or delete a specific collection with `/delete <collection_name>`

### Full Coding Project Generation Workflow (Beta)

* Use the `--create-project` flag or the `/project` command in the default chat interface.

**Complete workflow:**

* Asks for your project idea.
* Runs the ***Brainstormer Agent*** to create the context space and full project specification for the ***Codegen Agent*** (in `.md` format).
* Optionally lets you provide more context by chatting interactively with the ***Brainstormer Agent***.
* Runs the ***Codegen Agent*** using the generated `.md` files.
* Opens an interactive chat with the ***Codegen Agent*** to refine or extend the project.

This workflow is still in its early stages.

## Setup

### Prerequesites:

- [Python](https://www.python.org/)
- [Git](https://git-scm.com/downloads) (or download the source code from this repo)
- [Ollama](https://ollama.com/download)

### 1. Clone the Repo

In your chosen installation folder, open a terminal window and run:

```bash
git clone https://github.com/YassWorks/Ally.git
```

### 2. Configure `config.json`

This file (located at `Ally/`) controls Ally's main settings and integrations. 

**Example configuration:**

```json
{
    "provider": "openai",
    "provider_per_model": {
        "general": "ollama",
        "code_gen": "anthropic",
        "brainstormer": null,  // autofilled with 'openai'
        "web_searcher": null   // autofilled with 'openai'
    },

    "model": "gpt-4o",
    "models": {
        "general": "gpt-oss:20b",
        "code_gen": "claude-sonnet-3.5",
        "brainstormer": null,  // autofilled with 'gpt-4o'
        "web_searcher": null   // autofilled with 'gpt-4o'
    },
    
    "temperatures": {
        "general": 0.7,
        "code_gen": 0,
        "brainstormer": 1,
        "web_searcher": 0
    },
    "system_prompts": {  // (recommended) leave as-is to use Ally's defaults
        "general": null,
        "code_gen": null,
        "brainstormer": null,
        "web_searcher": null
    },

    "embedding_provider": null,  // example: "hf" or "ollama"
    "embedding_model": null,     // example: "sentence-transformers/all-MiniLM-L6-v2" or "all-minilm"
}
```

### 3. Configure `.env`

This file stores your API keys.

```
# Inference providers (only include those you need)

OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_GEN_AI_API_KEY=your_google_gen_ai_api_key_here
CEREBRAS_API_KEY=your_api_key_here

# Google Search API (if omitted, online search tools will be limited)

GOOGLE_SEARCH_API_KEY=your_google_api_key_here
SEARCH_ENGINE_ID=your_search_engine_id_here
```

Steps:

1. Set up a Google [Programmable Search Engine](https://developers.google.com/custom-search/v1/overview)
2. Copy the contents above (or from `.env.example`) into `.env`.
3. Fill in your API keys and IDs.

### 4. Run setup executable

Depending on your OS choose either `setup.cmd` (Windows) or `setup.sh` (Linux/Mac)

***Note:*** Ally creates its own virtual environment to keep dependencies isolated and automatically adds itself to your PATH.

Now you’re ready to run Ally from anywhere in the terminal using `ally`.

Use `ally -h` for more help.

## Technical notes

1. Edit the following environment variable if needed:  

| Environment Variable        | Purpose                                                      |
|-----------------------------|--------------------------------------------------------------|
| `ALLY_HISTORY_DIR`          | Controls where Ally stores its history.                      |
| `ALLY_DATABASE_DIR`         | Controls where Ally stores its database.                     |
| `ALLY_EMBEDDING_MODELS_DIR` | Controls where Ally stores its embedding models (Hugging Face). |
| `ALLY_PARSING_MODELS_DIR`   | Controls where Ally stores its parsing models used by Docling. |

Defaults are:
```
Windows:
%LOCALAPPDATA%\Ally\...

Linux & MacOS:
~/.local/share/Ally/...
```

2. RAG-related tools used by Ally are large in size and are therefore downloaded only after RAG settings are enabled in the config.json file. As a result, Ally will perform additional downloads the next time it is launched following these configuration changes.

3. To save a chat, use /id to view the conversation ID. The next time you open Ally, continue the conversation by using the -i flag followed by the ID.

4. Embedding and scraping files that require OCR (such as PDFs and DOCX) currently use a CPU-only PyTorch installation. You can modify the configuration to utilize a GPU if desired, though this is typically only necessary for processing very large files.

## License

Apache-2.0

---
Issues are always welcome 💌

Contact me via email to discuss contributions or collaborations on other projects if you liked my work!
