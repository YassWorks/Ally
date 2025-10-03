from app.utils.constants import CHUNK_SIZE, CHUNK_OVERLAP, DEFAULT_PATHS
from app.src.embeddings.scrapers.scraper import scrape_file, get_hash
from app.src.helpers.valid_dir import validate_dir_name
from app.src.embeddings.rag_errors import DBAccessError, ScrapingFailedError
from app.src.core.ui import default_ui
from app.utils.ui_messages import UI_MESSAGES
from typing import Callable, Any
from pathlib import Path
from datetime import datetime
import json
import os


# configure database path
DB_PATH = ""
if "ALLY_DATABASE_DIR" in os.environ:
    DB_PATH = Path(os.getenv("ALLY_DATABASE_DIR"))
    if not validate_dir_name(str(DB_PATH)):
        DB_PATH = ""
        default_ui.warning(
            UI_MESSAGES["warnings"]["invalid_db_path"]
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
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            with default_ui.console.status(
                "Installing additional required packages..."
            ):
                try:
                    import subprocess
                    import sys

                    # in case the user didn't setup RAG from the beginning
                    # we lazy-install chromadb & docling when needed
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "chromadb", "-qqq"]
                    )
                    subprocess.check_call(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "docling",
                            "--extra-index-url",
                            "https://download.pytorch.org/whl/cpu",  # CPU-only PyTorch for smaller download
                            "-qqq",
                        ]
                    )
                    
                except Exception as e:
                    default_ui.error(
                        UI_MESSAGES["errors"]["failed_install_packages"].format(e)
                    )
                    raise DBAccessError()
            import chromadb
            from chromadb.config import Settings

        self.db_client = chromadb.PersistentClient(
            path=DB_PATH, settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_function = embedding_function

        # Store indexed collections JSON file in the same database folder
        self.indexed_collections_path = DB_PATH / "indexed_collections.json"
        self._ensure_db_directory_exists()
        if not self.indexed_collections_path.exists():
            self.indexed_collections_path.write_text("{}")

        self.indexed_collections: dict[str, bool] = self._load_indexed_collections()

    @staticmethod
    def get_instance() -> "DataBaseClient":
        """Get the singleton instance of DataBaseClient."""
        if DataBaseClient._instance is None:
            return None
        return DataBaseClient._instance

    def _ensure_db_directory_exists(self) -> None:
        """Ensure the database directory exists."""
        try:
            DB_PATH.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            default_ui.error(UI_MESSAGES["errors"]["failed_create_db_directory"].format(e))
            raise

    def _load_indexed_collections(self) -> dict[str, bool]:
        """Load indexed collections from the JSON file."""
        try:
            with open(self.indexed_collections_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_indexed_collections(self) -> None:
        """Save indexed collections to the JSON file."""
        try:
            # Ensure the database directory exists before writing
            self._ensure_db_directory_exists()
            with open(self.indexed_collections_path, "w") as f:
                json.dump(self.indexed_collections, f, indent=2)
        except Exception as e:
            default_ui.error(UI_MESSAGES["errors"]["failed_save_indexed"].format(e))

    def index_collection(self, collection_name: str) -> None:
        """Mark a collection as indexed."""
        self.indexed_collections[collection_name] = True
        self._save_indexed_collections()

    def unindex_collection(self, collection_name: str) -> None:
        """Mark a collection as unindexed."""
        if collection_name in self.indexed_collections:
            self.indexed_collections[collection_name] = False
            self._save_indexed_collections()

    def already_stored(self, file_path: str, collection_name: str) -> bool:
        """Check if a document is already stored in the database."""
        import chromadb.errors as chromadb_errors

        try:
            collection = self.db_client.get_collection(name=collection_name)

        except chromadb_errors.NotFoundError:
            return False

        except Exception:
            raise DBAccessError()

        try:
            results = collection.get(
                where={"file_path": file_path},
                limit=1,
            )
            return bool(results["metadatas"])

        except Exception:
            raise DBAccessError()

    def store_document(self, file_path: str, collection_name: str) -> None:
        """Store document content and metadata in ChromaDB."""
        if self.already_stored(file_path, collection_name):
            return

        response = scrape_file(file_path)
        content = response["content"]
        metadata = response["metadata"]

        chunks = [
            content[i : i + CHUNK_SIZE]
            for i in range(0, len(content), CHUNK_SIZE - CHUNK_OVERLAP)
        ]

        if collection_name not in self.indexed_collections:
            self.indexed_collections[collection_name] = True  # default to indexed
            self._save_indexed_collections()

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
        import chromadb.errors as chromadb_errors

        last_hash = get_hash(file_path)
        last_mod_date = datetime.fromtimestamp(
            Path(file_path).stat().st_mtime
        ).isoformat()

        try:
            collection = self.db_client.get_collection(name=collection_name)

        except chromadb_errors.NotFoundError:
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

        if not validate_dir_name(directory_path):
            default_ui.error(UI_MESSAGES["errors"]["invalid_directory_path"].format(directory_path))
            return

        # Normalize the path
        directory_path = Path(directory_path)

        if os.name == "nt":
            directory_path = Path(os.path.expandvars(str(directory_path)))
        else:
            directory_path = Path(os.path.expanduser(str(directory_path)))

        directory_path = directory_path.resolve()
        directory_path = str(directory_path)

        # If it's a file, just process that single file
        if os.path.isfile(directory_path):
            try:
                if self.was_modified(directory_path, collection_name):
                    self.store_document(directory_path, collection_name)

            except ScrapingFailedError:
                default_ui.error(UI_MESSAGES["errors"]["failed_scrape"].format(directory_path))

            except:
                raise

        if not os.path.exists(directory_path):
            default_ui.error(UI_MESSAGES["errors"]["directory_not_exist"].format(directory_path))
            return

        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if self.was_modified(file_path, collection_name):
                        self.store_document(file_path, collection_name)

                except ScrapingFailedError:
                    default_ui.error(UI_MESSAGES["errors"]["failed_scrape"].format(file_path))

                except:
                    raise

        default_ui.status_message(
            title=UI_MESSAGES["titles"]["info"],
            message=UI_MESSAGES["success"]["documents_embedded"].format(directory_path, collection_name),
            style="success",
        )

    def delete_collection(
        self, collection_name: str
    ) -> None:
        """Delete a collection from the database."""
        import chromadb.errors as chromadb_errors

        if not default_ui.confirm(
            UI_MESSAGES["confirmations"]["delete_collection"].format(collection_name),
            default=False,
        ):
            return

        try:
            self.db_client.delete_collection(name=collection_name)
            # Remove from indexed collections and save
            if collection_name in self.indexed_collections:
                del self.indexed_collections[collection_name]
                self._save_indexed_collections()

        except chromadb_errors.NotFoundError:
            default_ui.error(UI_MESSAGES["errors"]["collection_not_exist"].format(collection_name))

        except Exception:
            raise DBAccessError()

    def list_collections(self) -> list:
        """List all collections in the database."""
        try:
            collections = self.db_client.list_collections()
            # answer in the format "- collection_name: is_indexed"
            lines = [
                f"• {col.name}: {'Indexed' if self.indexed_collections.get(col.name, False) else 'Unindexed'}"
                for col in collections
            ]
            listed_collections = (
                UI_MESSAGES["messages"]["collections_header"] + "\n" + "─" * 22 + "\n" + "\n".join(lines)
            )
            default_ui.status_message(
                title=UI_MESSAGES["titles"]["collections"], message=listed_collections, style="success"
            )

        except Exception:
            raise DBAccessError()

    def reset_database(self) -> None:
        """Reset the entire database by deleting all collections."""
        if not default_ui.confirm(
            UI_MESSAGES["confirmations"]["reset_database"],
            default=False,
        ):
            return

        try:
            collections = self.db_client.list_collections()
            for col in collections:
                self.db_client.delete_collection(name=col.name)
            # Clear indexed collections and save
            self.indexed_collections.clear()
            self._save_indexed_collections()
            default_ui.status_message(
                title=UI_MESSAGES["titles"]["database_reset"],
                message=UI_MESSAGES["messages"]["all_collections_deleted"],
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
        import chromadb.errors as chromadb_errors

        try:
            collection = self.db_client.get_collection(name=collection_name)

        except chromadb_errors.NotFoundError:
            default_ui.error(UI_MESSAGES["errors"]["collection_not_exist"].format(collection_name))
            return []

        except Exception:
            raise DBAccessError()

        try:
            results = collection.query(
                query_embeddings=self.embedding_function([query]),
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
