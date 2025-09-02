from app import CLI
from dotenv import load_dotenv
import os
import sys

load_dotenv()
cerebras_api_key = os.environ["CEREBRAS_API_KEY"] or os.getenv("CEREBRAS_API_KEY")
google_gen_ai_api_key = os.environ["GOOGLE_GEN_AI_API_KEY"] or os.getenv("GOOGLE_GEN_AI_API_KEY")

if not cerebras_api_key:
    print("Error: CEREBRAS_API_KEY environment variable not found")
    exit(1)

client = CLI(
    stream=True,
    api_key=cerebras_api_key,
    models={
        "general": "qwen-3-32b",
        "code_gen": "qwen-3-32b",
        "brainstormer": "qwen-3-32b",
        "web_searcher": "qwen-3-32b",
    },
    temperatures={
        "general": 0.7,
        "code_gen": 0,
        "brainstormer": 0.7,
        "web_searcher": 0,
    },
    provider="cerebras",
)

if __name__ == "__main__":
    
    args = sys.argv[1:]
    client.start_chat(*args)
