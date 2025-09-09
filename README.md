# Ally 🗿

Ally is an AI-powered CLI tool designed to assist with anything from everyday tasks to complex projects.

I built Ally to be a fully local agentic system using **Ollama**, but it also works seamlessly with:

* OpenAI
* Anthropic
* Google GenAI
* Cerebras
* *(with more integrations on the way!)*

This tool is best suited for scenarios where privacy is paramount and agentic capabilities are needed in the workflow, such as in scientific research or law firms.

## Key Features

#### Default Chat Interface

A general-purpose agent that can:

* Read, write, modify, and delete files and directories.
* Access the internet.
* Execute commands and code.

  ***Note:*** Tools always ask for your permission before executing.

#### Full Coding Project Generation Workflow

* Use the `--create-project` flag or the `/project` command in the default chat interface.

**Complete workflow:**

* Asks for your project idea.
* Runs the ***Brainstormer Agent*** to create the context space and full project specification for the ***Codegen Agent*** (in `.md` format).
* Optionally lets you provide more context by chatting interactively with the ***Brainstormer Agent***.
* Runs the ***Codegen Agent*** using the generated `.md` files.
* Opens an interactive chat with the ***Codegen Agent*** to refine or extend the project.

## Tutorial

#### Prerequesites: simply [Python](https://www.python.org/)

### 1. Clone the Repo

In your chosen installation folder, open a terminal window and run:

```bash
git clone https://github.com/YassWorks/Ally.git
```

### 2. Configure `ally_config.json`

This file (located at `Ally/`) controls Ally's main settings and integrations. Example configuration:

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
    "system_prompts": {  // leave as-is to use Ally's defaults
        "general": null,
        "code_gen": null,
        "brainstormer": null,
        "web_searcher": null
    }
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

# Google Search API (if omitted, search tools will be limited)
GOOGLE_SEARCH_API_KEY=your_google_api_key_here
SEARCH_ENGINE_ID=your_search_engine_id_here
```

Steps:

1. Set up a Google [Programmable Search Engine](https://developers.google.com/custom-search/v1/overview)
2. Copy the contents above (or from `.env.example`) into `.env`.
3. Fill in your API keys and IDs.

### 4. Run setup

Depending on your OS choose either `setup.cmd` (Windows) or `setup.sh` (Linux/Mac)

***Note:*** Ally creates its own virtual environment to keep dependencies isolated and automatically adds itself to your PATH.

Now you’re ready to run Ally from anywhere in the terminal using `ally`.

Use `ally -h` for more help.

## Technical notes

You can set the environment variable `ALLY_HISTORY_DIR` to control where Ally stores its history.