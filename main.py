from app import CLI
from dotenv import load_dotenv
import os
import sys

load_dotenv()
api_key = os.getenv("CEREBRAS_API_KEY")

if not api_key:
    print("Error: CEREBRAS_API_KEY environment variable not found")
    exit(1)

client = CLI(
    stream=True,
    api_key=api_key,
    general_model_name="qwen-3-235b-a22b-thinking-2507",
    codegen_model_name="qwen-3-coder-480b",
    brainstormer_model_name="qwen-3-235b-a22b-thinking-2507",
    web_searcher_model_name="qwen-3-235b-a22b-thinking-2507",
    general_temperature=0.7,
    codegen_temperature=0,
    brainstormer_temperature=0.7,
    web_searcher_temperature=0,
)

if __name__ == "__main__":
    
    args = sys.argv[1:]
    client.start_chat(*args)
