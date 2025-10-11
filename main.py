from app import CLI, default_ui
from dotenv import load_dotenv
from warnings import filterwarnings
import os
import sys
import json
import logging


logging.basicConfig(level=logging.CRITICAL)
filterwarnings("ignore", category=Warning, module="torch")
filterwarnings("ignore", category=Warning, module="docling")
filterwarnings("ignore", category=Warning, module="huggingface_hub")


load_dotenv()


api_keys = {
    "cerebras": os.getenv("CEREBRAS_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "google": os.getenv("GOOGLE_GEN_AI_API_KEY")
}


########### load the configuration ###########

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.json")
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    default_ui.error("Configuration file 'config.json' not found.")
    sys.exit(1)
except json.JSONDecodeError:
    default_ui.error("Configuration file 'config.json' is not a valid JSON.")
    sys.exit(1)
except Exception as e:
    default_ui.error(f"An unexpected error occurred: {e}")
    sys.exit(1)


AGENT_TYPES = ["general", "code_gen", "brainstormer", "web_searcher"]


########### prepare the configuration ###########

provider = config.get("provider")
model = config.get("model")
api_key = api_keys.get(provider)

raw_provider_per_model = config.get("provider_per_model") or {}
provider_per_model = {k: (raw_provider_per_model.get(k) or provider) for k in AGENT_TYPES}

raw_models = config.get("models") or {}
models = {k: (raw_models.get(k) or model) for k in AGENT_TYPES}

api_key_per_model = {k: api_keys.get(provider_per_model.get(k), api_key) for k in AGENT_TYPES}

temperatures = config.get("temperatures") or {}
system_prompts = config.get("system_prompts") or {}

embedding_provider = config.get("embedding_provider") or ""
embedding_model = config.get("embedding_model") or ""


client = CLI(
    provider=provider,
    provider_per_model=provider_per_model,
    models=models,
    api_key=api_key,
    api_key_per_model=api_key_per_model,
    embedding_provider=embedding_provider,
    embedding_model=embedding_model,
    temperatures=temperatures,
    system_prompts=system_prompts,
    stream=True,
)


########### run the CLI ###########

def main():
    args = sys.argv[1:]
    client.start_chat(*args)

if __name__ == "__main__":
    main()
