from app.src.cli.cli import DB_CLIENT
from app.src.core.ui import default_ui
import os


def handle_embed_request(*args):
    """Handle the /embed command to embed documents from a specified directory."""
    if DB_CLIENT is None:
        default_ui.error("Database client is not initialized.")
        return
    
    if len(args) < 2:
        default_ui.error("Usage: /embed <directory_path> <collection_name>")
        return

    directory_path = args[0]
    collection_name = args[1]
    
    if (directory_path == '.' or directory_path == "./"):
        directory_path = os.getcwd()
    
    DB_CLIENT.store_documents(directory_path, collection_name)


def handle_start_rag_request(*args):
    raise NotImplementedError("RAG functionality is not yet implemented.")


def handle_stop_rag_request(*args):
    raise NotImplementedError("RAG functionality is not yet implemented.")
