import hashlib

import pytest

from app.src.embeddings import db_client as db_module
from app.src.embeddings.db_client import DataBaseClient, split_into_chunks
from app.src.embeddings.scrapers.simple_scraper import SimpleScraper
from app.utils.constants import CHUNK_SIZE


class CountingEmbedder:
    def __init__(self):
        self.texts: list[str] = []

    def __call__(self, texts):
        self.texts.extend(texts)
        return [self._vector(text) for text in texts]

    @staticmethod
    def _vector(text):
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [byte / 255 for byte in digest[:16]]


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("ALLY_DATABASE_DIR", str(tmp_path / "db"))
    monkeypatch.setattr(DataBaseClient, "_instance", None)
    monkeypatch.setattr(db_module.default_ui, "status_message", lambda *a, **k: None)
    embedder = CountingEmbedder()
    client = DataBaseClient(embedding_function=embedder, scraper=SimpleScraper())
    return client, embedder


@pytest.fixture
def docs(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.md").write_text("alpha " * 400, encoding="utf-8")
    (folder / "b.txt").write_text("bravo notes", encoding="utf-8")
    return folder


def stored_chunks(client, collection="notes"):
    return client.db_client.get_collection(collection).get()["documents"]


def test_chunks_are_large_and_overlap():
    chunks = split_into_chunks("x" * 2500)

    assert len(chunks[0]) == CHUNK_SIZE
    assert len(chunks) == 4


def test_unchanged_files_are_not_embedded_again(db, docs):
    client, embedder = db
    client.store_documents(str(docs), "notes")
    first = len(embedder.texts)

    client.store_documents(str(docs), "notes")

    assert first > 0
    assert len(embedder.texts) == first


def test_modified_files_replace_their_old_chunks(db, docs):
    client, embedder = db
    client.store_documents(str(docs), "notes")

    (docs / "b.txt").write_text("charlie notes", encoding="utf-8")
    client.store_documents(str(docs), "notes")

    documents = stored_chunks(client)
    assert "charlie notes" in documents
    assert "bravo notes" not in documents


def test_empty_files_and_ignored_dirs_are_skipped(db, docs):
    client, embedder = db
    (docs / "empty.txt").write_text("", encoding="utf-8")
    (docs / ".git").mkdir()
    (docs / ".git" / "config").write_text("secret", encoding="utf-8")

    client.store_documents(str(docs), "notes")

    assert "secret" not in stored_chunks(client)


def test_identical_files_in_different_places_are_both_kept(db, docs):
    client, _ = db
    (docs / "copy.txt").write_text("bravo notes", encoding="utf-8")

    client.store_documents(str(docs), "notes")

    paths = {
        meta["file_path"]
        for meta in client.db_client.get_collection("notes").get()["metadatas"]
    }
    assert {p.rsplit("/", 1)[-1] for p in paths} == {"a.md", "b.txt", "copy.txt"}


def test_query_returns_several_chunks_from_one_file(db, docs):
    client, embedder = db
    client.store_documents(str(docs), "notes")
    calls_before = len(embedder.texts)

    results = client.get_query_results("alpha", n_results=3)

    assert len(results) == 3
    assert len(embedder.texts) == calls_before + 1
