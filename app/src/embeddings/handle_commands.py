from app.src.embeddings.db_client import DataBaseClient
from app.src.core.ui import default_ui
import os


def handle_embed_request(*args):
    """Handle the /embed command to embed documents from a specified directory."""
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error("Database client is not initialized.")
        return
    
    if len(args) < 2:
        default_ui.error("Usage: /embed <directory_path> <collection_name>")
        return

    directory_path = args[0]
    collection_name = args[1]
    
    if (directory_path == '.' or directory_path == "./"):
        directory_path = os.getcwd()
    
    db_client.store_documents(directory_path, collection_name)
