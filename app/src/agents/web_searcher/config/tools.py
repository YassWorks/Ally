from langchain_core.tools import tool
from typing import List, Dict
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[5]
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


GGL_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
CX_ID = os.getenv("SEARCH_ENGINE_ID")

# Validate environment variables early
if not GGL_API_KEY:
    print("WARNING: GOOGLE_SEARCH_API_KEY not set in .env file. Web search functionality will be limited.")
if not CX_ID:
    print("WARNING: SEARCH_ENGINE_ID not set in .env file. Web search functionality will be limited.")


ENDPOINT = "https://customsearch.googleapis.com/customsearch/v1"
TIMEOUT = 10  # seconds


def google_search(query: str, n: int = 5) -> List[Dict[str, str]]:
    """Search Google and return structured results.
    
    Args:
        query: Search query string
        n: Maximum number of results to return
        
    Returns:
        List of dictionaries with 'title' and 'link' keys
        
    Raises:
        ValueError: If API key or search engine ID not configured
        requests.HTTPError: If search request fails
    """

    if not GGL_API_KEY or not CX_ID:
        raise ValueError(
            "Google API key or Search Engine ID not set in .env file. "
            "Please set GOOGLE_SEARCH_API_KEY and SEARCH_ENGINE_ID environment variables."
        )

    results, start = [], 1
    while len(results) < n:
        batch = min(10, n - len(results))
        payload = {
            "key": GGL_API_KEY,
            "cx": CX_ID,
            "q": query,
            "num": batch,
            "start": start,
        }
        resp = requests.get(ENDPOINT, params=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("items", []):
            results.append(
                {
                    "title": item["title"],
                    "link": item["link"],
                }
            )
            if len(results) == n:
                break

        # prepare next page (if any)
        start += batch
        if "nextPage" not in data.get("queries", {}):
            break

    return results


def fetch_page_text(url: str) -> str:
    """Extract text content from a web page.
    
    Args:
        url: URL to scrape
        
    Returns:
        Cleaned text content (max 1000 chars) or error message
    """

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        # kill script/style
        for s in soup(["script", "style", "noscript"]):
            s.decompose()
        text = soup.get_text(separator=" ")
        res = ("\n".join(line.strip() for line in text.splitlines() if line.strip()))[
            :1000
        ]
        return res

    except Exception as e:
        return f"[ERROR] Failed to scrape {url}: {str(e)}"


@tool
def search_and_scrape(query: str) -> str:
    """
    Search Google for a query and get the top results structured as "title" and "content".
    This tool is used to extract information from all sources across the web.
    Args:
        query (str): The search query to use.
    """
    try:
        search_results = google_search(query, 5)
        for r in search_results:
            r["full_text"] = fetch_page_text(r["link"])

        formatted_results = "This answer is possibly incomplete. Consider refining search terms if needed.\n\n"
        # search_results has "title" and "full_text" keys. Let's structure it nicely for the agent:
        for r in search_results:
            formatted_results += f"Title: {r['title']}\n"
            formatted_results += f"Content: {r['full_text']}\n\n"

        return formatted_results
    except Exception as e:
        return f"[ERROR] Failed to perform web search: {str(e)}"
