from app.utils.constants import CHUNK_SIZE, CHUNK_OVERLAP, DEFAULT_PATHS
from app.src.embeddings.scrapers.scraper import scrape_file, get_hash
from app.src.helpers.valid_dir import validate_dir_name
from app.src.embeddings.rag_errors import DBAccessError, ScrapingFailedError
from app.src.core.ui import default_ui
from chromadb.config import Settings
from typing import Callable, Any
from pathlib import Path
from datetime import datetime
import chromadb
import os


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
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, embedding_function: Callable = None) -> None:
        self.db_client = chromadb.PersistentClient(
            path=DB_PATH, settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_function = embedding_function
        self.indexed_collections: dict[str, bool] = {}  # collection_name -> is_indexed

    @staticmethod
    def get_instance() -> "DataBaseClient":
        """Get the singleton instance of DataBaseClient."""
        if DataBaseClient._instance is None:
            return None
        return DataBaseClient._instance

    def index_collection(self, collection_name: str) -> None:
        """Mark a collection as indexed."""
        self.indexed_collections[collection_name] = True

    def unindex_collection(self, collection_name: str) -> None:
        """Mark a collection as unindexed."""
        if collection_name in self.indexed_collections:
            self.indexed_collections[collection_name] = False

    def store_document(self, file_path: str, collection_name: str) -> None:
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
        )

        collection.add(
            documents=chunks,
            metadatas=[metadata] * len(chunks),
            embeddings=self.embedding_function(chunks),
            ids=[f"{metadata['hash']}_{i}" for i in range(len(chunks))],
        )

    def was_modified(self, file_path: str, collection_name: str) -> bool:
        """Check if the file has been modified by comparing hashes and modification dates."""

        last_hash = get_hash(file_path)
        last_mod_date = datetime.fromtimestamp(
            Path(file_path).stat().st_mtime
        ).isoformat()

        try:
            collection = self.db_client.get_collection(name=collection_name)

        except chromadb.errors.NotFoundError:
            return True

        except Exception:
            raise DBAccessError()

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

            stored_hash, stored_mod_date = (
                results["metadatas"][0].get("hash") if results["metadatas"] else None,
                (
                    results["metadatas"][0].get("mod_date")
                    if results["metadatas"]
                    else None
                ),
            )

            if stored_hash is None or stored_mod_date is None:
                return True

        except Exception:
            raise DBAccessError()

        return last_hash != stored_hash or last_mod_date != stored_mod_date

    def store_documents(self, directory_path: str, collection_name: str) -> None:
        """Store all documents from a directory into the database."""

        if not os.path.exists(directory_path):
            default_ui.error(f"Directory {directory_path} does not exist.")
            return

        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if self.was_modified(file_path, collection_name):
                        self.store_document(file_path, collection_name)

                except ScrapingFailedError:
                    default_ui.error(f"Failed to scrape file: {file_path}. Skipping.")

                except:
                    raise

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection from the database."""
        if not default_ui.confirm(
            f"Are you sure you want to delete the collection '{collection_name}'?",
            default=False,
        ):
            return

        try:
            self.db_client.delete_collection(name=collection_name)

        except chromadb.errors.NotFoundError:
            default_ui.error(f"Collection {collection_name} does not exist.")

        except Exception:
            raise DBAccessError()

    def list_collections(self) -> list:
        """List all collections in the database."""
        try:
            collections = self.db_client.list_collections()
            # answer in the format "- collection_name: is_indexed"
            listed_collections = f"""
            Collections available:
            ----------------------
            {'\n-'.join([f"`{col.name}`: {"Indexed" if self.indexed_collections.get(col.name, False) else "Unindexed"}" for col in collections])}
            """
            default_ui.status_message(
                title="Collections", message=listed_collections, style="success"
            )

        except Exception:
            raise DBAccessError()

    def reset_database(self) -> None:
        """Reset the entire database by deleting all collections."""
        if not default_ui.confirm(
            "Are you sure you want to reset the database? This action cannot be undone.",
            default=False,
        ):
            return

        try:
            collections = self.db_client.list_collections()
            for col in collections:
                self.db_client.delete_collection(name=col.name)
            default_ui.status_message(
                title="Database Reset",
                message="All collections have been deleted.",
                style="success",
            )

        except Exception:
            raise DBAccessError()

    def get_query_results(
        self, query: str, n_results: int = 5
    ) -> list[tuple[str, dict[str, Any]]]:
        """Query the database and return relevant documents."""
        candidates = []
        # getting the closest documents across the given collections
        for collection_name in self.indexed_collections.keys():
            if not self.indexed_collections[collection_name]:
                continue
            
            candidates.extend(
                self.get_query_results_from_collection(
                    query, collection_name.strip(), n_results
                )
            )

        # merging and sorting the results by distance
        candidates.sort(key=lambda x: x[2])
        query_results = [(doc, meta) for doc, meta, _ in candidates[:n_results]]
        
        return query_results

    def get_query_results_from_collection(
        self, query: str, collection_name: str, n_results: int = 5
    ) -> list[tuple[str, dict[str, Any], float]]:
        """Query the database and return relevant documents."""
        try:
            collection = self.db_client.get_collection(name=collection_name)

        except chromadb.errors.NotFoundError:
            default_ui.error(f"Collection {collection_name} does not exist.")
            return []

        except Exception:
            raise DBAccessError()

        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
            return list(
                zip(
                    results.get("documents", [[]])[0],
                    results.get("metadatas", [[]])[0],
                    results.get("distances", [[]])[0],
                )
            )

        except Exception:
            raise DBAccessError()
