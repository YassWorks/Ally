from concurrent.futures import ThreadPoolExecutor

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
        soup = BeautifulSoup(resp.content, "lxml")

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


@tool(parse_docstring=True)
def fetch_tool(url: str) -> str:
    """Download a web page and return its readable text.

    Use it only when you already have the URL; it does not search. Scripts,
    styles, headers and footers are removed and the text is cut at 10,000
    characters.

    Args:
        url: Full address of the page, including http:// or https://.
    """
    return fetch(url)


SEARCH_RESULTS = 5
SEARCH_TIMEOUT = 10
SEARCH_PAGE_CHARS = 4000


def web_search(query: str, n: int = SEARCH_RESULTS) -> list[dict[str, str]]:
    """Return up to ``n`` web results for ``query`` as ``{"title", "link"}`` dicts.

    Uses the ddgs metasearch library, which needs no API key.

    Raises:
        ddgs.exceptions.DDGSException: If the search fails or finds nothing.
    """
    from ddgs import DDGS

    results = DDGS(timeout=SEARCH_TIMEOUT).text(query, max_results=n)
    return [{"title": r["title"], "link": r["href"]} for r in results[:n]]


@tool(parse_docstring=True)
def search_and_scrape(query: str) -> str:
    """Search the web and return the text of the top 5 results.

    Each result starts with its title and URL, followed by the first 4,000
    characters of the page. Use fetch_tool on a result's URL to read more of
    it. If the results miss the point, search again with different terms.

    Args:
        query: Search terms.
    """
    try:
        results = web_search(query)
    except Exception as e:
        logger.warning(f"Web search failed: {query}", exc_info=e)
        reason = str(e).rstrip(".") or type(e).__name__
        return f"Web search failed: {reason}. Try different search terms."

    with ThreadPoolExecutor(max_workers=len(results) or 1) as pool:
        pages = list(pool.map(fetch, [r["link"] for r in results]))

    sections = [
        f"# {r['title']}\nSource: {r['link']}\n\n{text[:SEARCH_PAGE_CHARS]}"
        for r, text in zip(results, pages, strict=True)
    ]
    return "\n\n".join(sections)
