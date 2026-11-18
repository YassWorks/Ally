import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.src.core.ui import default_ui
from app.src.embeddings.rag_errors import DBAccessError, ScrapingFailedError
from app.src.embeddings.scrapers.abstract_scraper import Scraper
from app.src.helpers.valid_dir import validate_dir_name
from app.src.tools.find_tools import IGNORED_DIRS
from app.utils.constants import BATCH_SIZE, CHUNK_OVERLAP, CHUNK_SIZE, MAX_RESULTS
from app.utils.logger import logger
from app.utils.paths import data_dir
from app.utils.ui_messages import UI_MESSAGES


def path_key(file_path: str | Path) -> str:
    """Return the form of ``file_path`` stored in chunk metadata."""
    return Path(file_path).as_posix()


def split_into_chunks(
    text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """Split ``text`` into chunks of ``size`` characters that overlap by ``overlap``."""
    step = max(size - overlap, 1)
    return [text[i : i + size] for i in range(0, len(text), step)]


class DataBaseClient:
    """Process-wide ChromaDB store for RAG collections.

    Args:
        embedding_function: Turns a list of texts into a list of vectors.
        scraper: Extracts text and metadata from files.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self, embedding_function: Callable | None = None, scraper: Scraper | None = None
    ):
        import chromadb
        from chromadb.config import Settings

        self.db_path = data_dir("database", "ALLY_DATABASE_DIR")
        self.db_client = chromadb.PersistentClient(
            path=self.db_path, settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_function = embedding_function
        self.scraper = scraper

        self.indexed_collections_path = self.db_path / "indexed_collections.json"
        if not self.indexed_collections_path.exists():
            self.indexed_collections_path.write_text("{}", encoding="utf-8")
        self.indexed_collections: dict[str, bool] = self._load_indexed_collections()

    @staticmethod
    def get_instance() -> "DataBaseClient | None":
        """Return the client created at startup, or ``None`` if RAG is not configured."""
        return DataBaseClient._instance

    def _load_indexed_collections(self) -> dict[str, bool]:
        try:
            return json.loads(self.indexed_collections_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_indexed_collections(self) -> None:
        try:
            self.indexed_collections_path.write_text(
                json.dumps(self.indexed_collections, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.error("Failed to save indexed collections", exc_info=e)
            default_ui.error(UI_MESSAGES["errors"]["failed_save_indexed"])

    def _get_collection(self, collection_name: str):
        import chromadb.errors as chromadb_errors

        try:
            return self.db_client.get_collection(name=collection_name)
        except chromadb_errors.NotFoundError:
            return None
        except Exception as e:
            raise DBAccessError() from e

    def index_collection(self, collection_name: str) -> None:
        """Include ``collection_name`` in RAG lookups."""
        self.indexed_collections[collection_name] = True
        self._save_indexed_collections()

    def unindex_collection(self, collection_name: str) -> None:
        """Leave ``collection_name`` out of RAG lookups without deleting it."""
        if collection_name in self.indexed_collections:
            self.indexed_collections[collection_name] = False
            self._save_indexed_collections()

    def was_modified(self, file_path: str, collection_name: str) -> bool:
        """Return whether ``file_path`` is new or changed since it was last embedded."""
        collection = self._get_collection(collection_name)
        if collection is None:
            return True

        try:
            stored = collection.get(where={"file_path": path_key(file_path)}, limit=1)
        except Exception as e:
            raise DBAccessError() from e

        if not stored["metadatas"]:
            return True
        return stored["metadatas"][0].get("hash") != self.scraper.get_hash(file_path)

    def store_document(self, file_path: str, collection_name: str) -> None:
        """Embed ``file_path`` into ``collection_name``, replacing any older version of it."""
        response = self.scraper.scrape(file_path)
        metadata = {**response["metadata"], "file_path": path_key(file_path)}
        chunks = split_into_chunks(response["content"])

        if collection_name not in self.indexed_collections:
            self.index_collection(collection_name)

        collection = self.db_client.get_or_create_collection(name=collection_name)
        collection.delete(where={"file_path": metadata["file_path"]})

        if not chunks:
            logger.info(f"Skipping empty file: {file_path}")
            return

        embeddings = []
        for i in range(0, len(chunks), BATCH_SIZE):
            embeddings.extend(self.embedding_function(chunks[i : i + BATCH_SIZE]))

        prefix = hashlib.sha1(metadata["file_path"].encode("utf-8")).hexdigest()[:16]
        collection.add(
            documents=chunks,
            metadatas=[metadata] * len(chunks),
            embeddings=embeddings,
            ids=[f"{prefix}_{i}" for i in range(len(chunks))],
        )

    def store_documents(self, directory_path: str, collection_name: str) -> None:
        """Embed a file, or every file under a directory, skipping unchanged ones."""
        if not validate_dir_name(directory_path):
            logger.error(f"Invalid directory path: {directory_path}")
            default_ui.error(UI_MESSAGES["errors"]["invalid_directory_path"])
            return

        root = Path(os.path.expanduser(os.path.expandvars(directory_path))).resolve()
        if not root.exists():
            logger.error(f"Directory does not exist: {root}")
            default_ui.error(UI_MESSAGES["errors"]["directory_not_exist"])
            return

        if root.is_file():
            files = [root]
        else:
            files = sorted(
                p
                for p in root.rglob("*")
                if p.is_file()
                and not IGNORED_DIRS.intersection(p.relative_to(root).parts[:-1])
            )
        for file_path in files:
            try:
                if self.was_modified(str(file_path), collection_name):
                    self.store_document(str(file_path), collection_name)
            except ScrapingFailedError as e:
                logger.error(f"Failed to scrape file: {file_path}", exc_info=e)
                default_ui.error(
                    f"{UI_MESSAGES['errors']['failed_scrape']} ({file_path.name})"
                )

        default_ui.status_message(
            title=UI_MESSAGES["titles"]["info"],
            message=UI_MESSAGES["success"]["documents_embedded"].format(
                root, collection_name
            ),
            style="success",
        )

    def delete_collection(self, collection_name: str) -> None:
        """Delete ``collection_name`` after asking the user to confirm."""
        import chromadb.errors as chromadb_errors

        if not default_ui.confirm(
            UI_MESSAGES["confirmations"]["delete_collection"].format(collection_name),
            default=False,
        ):
            return

        try:
            self.db_client.delete_collection(name=collection_name)
        except chromadb_errors.NotFoundError as e:
            logger.warning(f"Collection not found: {collection_name}", exc_info=e)
            default_ui.error(UI_MESSAGES["errors"]["collection_not_exist"])
            return
        except Exception as e:
            raise DBAccessError() from e

        if self.indexed_collections.pop(collection_name, None) is not None:
            self._save_indexed_collections()

        default_ui.status_message(
            title=UI_MESSAGES["titles"]["collection_deleted"],
            message=UI_MESSAGES["messages"]["collection_deleted"].format(
                collection_name
            ),
            style="success",
        )

    def list_collections(self) -> None:
        """Show every collection and whether it is indexed."""
        try:
            collections = self.db_client.list_collections()
        except Exception as e:
            raise DBAccessError() from e

        lines = [
            f"- {col.name}: "
            f"{'Indexed' if self.indexed_collections.get(col.name, False) else 'Unindexed'}"
            for col in collections
        ]
        default_ui.status_message(
            title=UI_MESSAGES["titles"]["collections"],
            message="\n".join(lines) if lines else "No collections found.",
            style="success",
        )

    def reset_database(self) -> None:
        """Delete every collection after asking the user to confirm."""
        if not default_ui.confirm(
            UI_MESSAGES["confirmations"]["reset_database"], default=False
        ):
            return

        try:
            for col in self.db_client.list_collections():
                self.db_client.delete_collection(name=col.name)
        except Exception as e:
            raise DBAccessError() from e

        self.indexed_collections.clear()
        self._save_indexed_collections()
        default_ui.status_message(
            title=UI_MESSAGES["titles"]["database_reset"],
            message=UI_MESSAGES["messages"]["all_collections_deleted"],
            style="success",
        )

    def get_query_results(
        self, query: str, n_results: int = MAX_RESULTS
    ) -> list[tuple[str, dict[str, Any]]]:
        """Return the ``n_results`` chunks closest to ``query`` across indexed collections."""
        names = [name for name, indexed in self.indexed_collections.items() if indexed]
        if not names:
            return []

        query_embedding = self.embedding_function([query])
        candidates = []
        for name in names:
            candidates.extend(
                self.get_query_results_from_collection(
                    query_embedding, name.strip(), n_results
                )
            )

        candidates.sort(key=lambda candidate: candidate[2])
        seen: set[str] = set()
        results = []
        for doc, meta, _ in candidates:
            if doc in seen:
                continue
            seen.add(doc)
            results.append((doc, meta))
        return results[:n_results]

    def get_query_results_from_collection(
        self,
        query_embedding: list[list[float]],
        collection_name: str,
        n_results: int = MAX_RESULTS,
    ) -> list[tuple[str, dict[str, Any], float]]:
        """Return ``(document, metadata, distance)`` matches from one collection."""
        collection = self._get_collection(collection_name)
        if collection is None:
            return []

        try:
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            raise DBAccessError() from e

        return list(
            zip(
                results.get("documents", [[]])[0],
                results.get("metadatas", [[]])[0],
                results.get("distances", [[]])[0],
                strict=False,
            )
        )
