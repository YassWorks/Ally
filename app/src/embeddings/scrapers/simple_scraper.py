from app.src.embeddings.scrapers.abstract_scraper import Scraper
from pathlib import Path


class SimpleScraper(Scraper):
    
    def scrape(self, file_path: str | Path) -> dict:
        ...
