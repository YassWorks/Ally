from app.utils.constants import CHUNK_SIZE, CHUNK_OVERLAP, DEFAULT_PATHS
from app.src.embeddings.scrapers.scraper import scrape_file
from app.src.core.ui import default_ui
from app.src.helpers.valid_dir import validate_dir_name
from typing import Callable
import chromadb
import sys
import os
from pathlib import Path


# configure database path
DB_PATH = ""
if "ALLY_DATABASE_DIR" in os.environ:
    DB_PATH = Path(os.getenv("ALLY_DATABASE_DIR"))
    if not validate_dir_name(str(DB_PATH)):
        DB_PATH = ""
        default_ui.warning(
            "Invalid directory path found in $ALLY_DATABASE_DIR. Reverting to default path."
        )

if not DB_PATH:
    DB_PATH = DEFAULT_PATHS["database"]
    if os.name == "nt":
        DB_PATH = Path(os.path.expandvars(DB_PATH))
    else:
        DB_PATH = Path(os.path.expanduser(DB_PATH))


class DataBaseClient:

    def __init__(self, path: str = None) -> None:
        if path is None:
            self.db_client = chromadb.Client()
        else:
            self.db_client = chromadb.PersistentClient(path=path)

    def store_document(
        self, file_path: str, collection_name: str, embedding_function: Callable
    ) -> None:
        """Store document content and metadata in ChromaDB."""

        response = scrape_file(file_path)
        content = response["content"]
        metadata = response["metadata"]

        chunks = [
            content[i : i + CHUNK_SIZE]
            for i in range(0, len(content), CHUNK_SIZE - CHUNK_OVERLAP)
        ]

        collection = self.db_client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

        collection.add(
            documents=chunks,
            metadatas=[metadata] * len(chunks),
            ids=[f"{metadata['hash']}_{i}" for i in range(len(chunks))],
        )

    def was_modified(self, file_path: str, collection_name: str) -> bool:
        """Check if the file has been modified by comparing hashes and modification dates."""

        response = scrape_file(file_path)
        last_hash = response["metadata"]["hash"]
        last_mod_date = response["metadata"]["mod_date"]

        try:
            collection = self.db_client.get_collection(name=collection_name)
            
        except chromadb.errors.NotFoundError:
            return True
        except Exception:
            default_ui.error("An error occurred while accessing the database.")
            sys.exit(1)

        try:
            # get documents by metadata hash to find any document with the same file path
            results = collection.get(
                where={"file_path": file_path},
                limit=1,
            )
            if not results[
                "metadatas"
            ]:  # File not found in collection, consider it as modified (new file)
                return True

            stored_hash = (
                results["metadatas"][0].get("hash") if results["metadatas"] else None
            )
            stored_mod_date = (
                results["metadatas"][0].get("mod_date")
                if results["metadatas"]
                else None
            )

            if stored_hash is None or stored_mod_date is None:
                return True

        except Exception:
            default_ui.error("An error occurred while accessing the database.")
            sys.exit(1)

        return last_hash != stored_hash or last_mod_date != stored_mod_date

    def store_documents(self, directory_path: str, collection_name: str, embedding_function: Callable) -> None:
        """Store all documents from a directory into the database."""

        if not os.path.exists(directory_path):
            default_ui.error(f"Directory {directory_path} does not exist.")
            return

        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if self.was_modified(file_path, collection_name):
                        self.store_document(file_path, collection_name, embedding_function)
                
                except ValueError:
                    continue
                except Exception:
                    default_ui.error(f"Failed to embed {file_path}")


# injectable singleton instance
db_client = DataBaseClient(path=db_path)
