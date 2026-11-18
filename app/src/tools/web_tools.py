import os

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from requests.adapters import HTTPAdapter, Retry

from app.utils.logger import logger


def fetch(url: str) -> str:
    """Fetch and extract main text content from a URL."""

    session = requests.Session()
    retries = Retry(
        total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }

    try:
        resp = session.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml")  # faster parser than html.parser

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "header",
                "footer",
                "svg",
                "img",
                "meta",
                "link",
            ]
        ):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())
        return text[:10000]

    except requests.RequestException as e:
        logger.error(f"HTTP error fetching {url}", exc_info=e)
        return f"[ERROR] HTTP error for {url}: {e}"
    except Exception as e:
        logger.error(f"Failed to parse {url}", exc_info=e)
        return f"[ERROR] Failed to parse {url}: {e}"


@tool
def fetch_tool(url: str) -> str:  # Wrapper to expose fetch as a LangChain tool
    """
    ## PRIMARY PURPOSE:
    Extract clean text content from web pages with automatic script/style removal.
    **ONLY USE when you have a specific URL and want to automatically access it.**

    ## WHEN TO USE:
    - **MUST have a specific, known URL that you want to automatically fetch content from**
    - Analyze content from URLs already discovered through search or provided by user
    - Extract documentation, tutorials, or technical information from known sources
    - Scrape articles, blog posts, or research content when URL is already available
    - Gather detailed information from specific web sources (not for searching)

    ## PARAMETERS:
        url (str): **Specific web page URL** to scrape and extract text content from

    ## RETURNS:
        str: Cleaned text content (max 10,000 chars) or error message if scraping fails
    """
    return fetch(url)


SEARCH_ENDPOINT = "https://customsearch.googleapis.com/customsearch/v1"
SEARCH_TIMEOUT = 10


def google_search(query: str, n: int = 5) -> list[dict[str, str]]:
    """Return up to ``n`` Google results for ``query`` as ``{"title", "link"}`` dicts.

    Raises:
        ValueError: If ``GOOGLE_SEARCH_API_KEY`` or ``SEARCH_ENGINE_ID`` is not set.
        requests.HTTPError: If the search request fails.
    """
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    engine_id = os.getenv("SEARCH_ENGINE_ID")
    if not api_key or not engine_id:
        raise ValueError(
            "Set GOOGLE_SEARCH_API_KEY and SEARCH_ENGINE_ID in .env to enable web search."
        )

    results, start = [], 1
    while len(results) < n:
        batch = min(10, n - len(results))
        params = {
            "key": api_key,
            "cx": engine_id,
            "q": query,
            "num": batch,
            "start": start,
        }
        resp = requests.get(SEARCH_ENDPOINT, params=params, timeout=SEARCH_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("items", []):
            results.append({"title": item["title"], "link": item["link"]})
            if len(results) == n:
                break

        start += batch
        if "nextPage" not in data.get("queries", {}):
            break

    return results


@tool
def search_and_scrape(query: str) -> str:
    """
    ## PRIMARY PURPOSE:
    Perform Google search and extract full text content from top 5 results.

    ## WHEN TO USE:
    - Research technical topics, best practices, or implementation approaches
    - Find current information about programming languages, frameworks, tools
    - Gather multiple perspectives and comprehensive information
    - Collect up-to-date tutorials, documentation, or guides

    ## PARAMETERS:
        query (str): Search query string to find relevant web pages

    ## RETURNS:
        str: Formatted results with titles and full text content from top search results
    """
    try:
        search_results = google_search(query, 5)
        for r in search_results:
            r["full_text"] = fetch(r["link"])

        formatted_results = "This answer is **possibly incomplete**. Consider refining search terms as needed.\n\n"
        for r in search_results:
            formatted_results += f"# Title: \n{r['title']}\n\n"
            formatted_results += f"# Content: \n{r['full_text']}\n\n"

        return formatted_results
    except Exception as e:
        return f"[ERROR] Failed to perform web search: {e}"
