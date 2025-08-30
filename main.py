from app import CLI
from dotenv import load_dotenv
import os
import sys

load_dotenv()
api_key = os.getenv("CEREBRAS_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: CEREBRAS_API_KEY environment variable not found")
    exit(1)

client = CLI(
    stream=True,
    api_key=api_key,
    models={
        "general": "gemini-2.5-flash",
        "code_gen": "qwen3:0.6b",
        "brainstormer": "qwen3:0.6b",
        "web_searcher": "qwen3:0.6b",
    },
    temperatures={
        "general": 0.7,
        "code_gen": 0,
        "brainstormer": 0.7,
        "web_searcher": 0,
    },
    provider="ollama",
    provider_per_model={
        "general": "google"
    },
    api_key_per_model={
        "general": google_api_key
    }
)

if __name__ == "__main__":
    
    args = sys.argv[1:]
    client.start_chat(*args)
