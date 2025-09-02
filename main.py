from app import CLI
from dotenv import load_dotenv
import os
import sys
import json


load_dotenv()

api_keys = {
    "cerebras": os.getenv("CEREBRAS_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "google_gen_ai": os.getenv("GOOGLE_GEN_AI_API_KEY")
}


########### load the configuration ###########

try:
    with open("D:\\Database\\Documents\\Programming\\PROJECTS\\Ally\\ally_config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Configuration file 'ally_config.json' not found.")
    sys.exit(1)
except json.JSONDecodeError:
    print("Configuration file 'ally_config.json' is not a valid JSON.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
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


client = CLI(
    provider=provider,
    provider_per_model=provider_per_model,
    models=models,
    api_key=api_key,
    api_key_per_model=api_key_per_model,
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
