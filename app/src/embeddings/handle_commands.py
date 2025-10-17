from app.src.embeddings.db_client import DataBaseClient
from app.src.core.ui import default_ui
from app.utils.ui_messages import UI_MESSAGES
import os


def handle_embed_request(*args):
    """Handle the /embed command to embed documents from a specified directory."""
    db_client = DataBaseClient.get_instance()

    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return

    if len(args) < 2:
        default_ui.error(UI_MESSAGES["usage"]["embed"])
        return

    directory_path = args[0]
    collection_name = args[1]

    if directory_path == "." or directory_path == "./":
        directory_path = os.getcwd()

    with default_ui.console.status("Embedding documents..."):
        db_client.store_documents(directory_path, collection_name)


def handle_index_request(*args):
    """Handle the /index command to toggle indexing for a specified collection."""
    db_client = DataBaseClient.get_instance()

    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return

    if len(args) < 1:
        default_ui.error(UI_MESSAGES["usage"]["index"])
        return

    collection_name = args[0]

    db_client.index_collection(collection_name)
    default_ui.status_message(
        title=UI_MESSAGES["titles"]["info"],
        message=UI_MESSAGES["success"]["collection_indexed"].format(collection_name),
        style="success",
    )


def handle_unindex_request(*args):
    """Handle the /unindex command to toggle indexing for a specified collection."""
    db_client = DataBaseClient.get_instance()

    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return

    if len(args) < 1:
        default_ui.error(UI_MESSAGES["usage"]["unindex"])
        return

    collection_name = args[0]

    db_client.unindex_collection(collection_name)
    default_ui.status_message(
        title=UI_MESSAGES["titles"]["info"],
        message=UI_MESSAGES["success"]["collection_unindexed"].format(collection_name),
        style="success",
    )


def handle_list_command(*args):
    """
    Handle the /list command which lists collections in the database and
    whether they are indexed or not.
    """
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return
    
    db_client.list_collections()


def handle_delete_command(*args):
    """Handles the deletion of a collection from the database by its name."""
    db_client = DataBaseClient.get_instance()
    
    if len(args) < 1:
        default_ui.error(UI_MESSAGES["usage"]["delete"])
        return
    
    collection_name = args[0]
    
    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return
    
    db_client.delete_collection(collection_name=collection_name)
    

def handle_purge_command():
    """Handles the purging of all collections from the database."""
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return
    
    db_client.reset_database()
