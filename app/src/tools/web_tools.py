from langchain_core.tools import tool
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
import requests


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
        return f"[ERROR] HTTP error for {url}: {e}"
    except Exception as e:
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
