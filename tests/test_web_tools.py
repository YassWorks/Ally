import sys
import types

import pytest

from app.src.tools import web_tools


class FakeDDGS:
    results: list[dict] = []
    error: Exception | None = None

    def __init__(self, timeout=None):
        self.timeout = timeout

    def text(self, query, max_results=None):
        if self.error:
            raise self.error
        return self.results


@pytest.fixture
def search(monkeypatch):
    monkeypatch.setitem(sys.modules, "ddgs", types.SimpleNamespace(DDGS=FakeDDGS))
    monkeypatch.setattr(FakeDDGS, "results", [])
    monkeypatch.setattr(FakeDDGS, "error", None)
    monkeypatch.setattr(web_tools, "fetch", lambda url: f"text of {url}")
    return FakeDDGS


def test_results_include_title_source_and_page_text(search):
    search.results = [
        {"title": "Python", "href": "https://python.org", "body": "..."},
        {"title": "Docs", "href": "https://docs.python.org", "body": "..."},
    ]

    result = web_tools.search_and_scrape.invoke({"query": "python"})

    assert result == (
        "# Python\nSource: https://python.org\n\ntext of https://python.org\n\n"
        "# Docs\nSource: https://docs.python.org\n\ntext of https://docs.python.org"
    )


def test_search_failures_are_reported_to_the_model(search):
    search.error = RuntimeError("No results found.")

    result = web_tools.search_and_scrape.invoke({"query": "zzzz"})

    assert result == "Web search failed: No results found. Try different search terms."


def test_each_result_page_is_kept_short(search, monkeypatch):
    search.results = [{"title": "Long", "href": "https://long.example", "body": ""}]
    monkeypatch.setattr(web_tools, "fetch", lambda url: "z" * 9000)

    result = web_tools.search_and_scrape.invoke({"query": "long"})

    assert result.count("z") == web_tools.SEARCH_PAGE_CHARS
