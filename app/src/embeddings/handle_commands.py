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


def handle_index_request(*args):
    """Handle the /index command to toggle indexing for a specified collection."""
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error("Database client is not initialized. There might be an issue with your embeddings config.")
        return
    
    if len(args) < 1:
        default_ui.error("Usage: /index <collection_name>")
        return

    collection_name = args[0]
    
    db_client.index_collection(collection_name)
    default_ui.status_message(title="Info", message=f"Collection '{collection_name}' is now indexed.", style="success")


def handle_unindex_request(*args):
    """Handle the /unindex command to toggle indexing for a specified collection."""
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error("Database client is not initialized. There might be an issue with your embeddings config.")
        return
    
    if len(args) < 1:
        default_ui.error("Usage: /unindex <collection_name>")
        return

    collection_name = args[0]
    
    db_client.unindex_collection(collection_name)
    default_ui.status_message(title="Info", message=f"Collection '{collection_name}' is now unindexed.", style="success")
