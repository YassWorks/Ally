from app.src.embeddings.scrapers.abstract_scraper import Scraper
from app.src.embeddings.rag_errors import ScrapingFailedError
from pathlib import Path

# docx
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

# pdf
import pymupdf4llm
import datetime


class SimpleScraper(Scraper):

    def scrape(self, file_path: str | Path) -> dict:
        """Extract text and metadata from a file using simple methods."""

        file_lower = str(file_path).lower()

        if file_lower.endswith(".pdf"):
            try:
                text = self._extract_pdf(file_path)
            except Exception as e:
                raise ScrapingFailedError(f"Failed to scrape PDF file: {e}")

        elif file_lower.endswith(".docx"):
            try:
                text = self._extract_docx(file_path)
            except Exception as e:
                raise ScrapingFailedError(f"Failed to scrape DOCX file: {e}")

        else:
            try:
                text = self.read_regular_file(file_path)
            except Exception as e:
                raise ScrapingFailedError(f"Failed to scrape file: {e}")

        text = text.strip()

        return {
            "content": text,
            "metadata": {
                "file_path": Path(file_path).as_posix(),
                "mod_date": datetime.datetime.fromtimestamp(
                    Path(file_path).stat().st_mtime
                ).isoformat(),
                "hash": self.get_hash(file_path),
            },
        }

    @staticmethod
    def _extract_pdf(file_path: str | Path) -> str:
        md = pymupdf4llm.to_markdown(file_path)
        return md.strip()

    @staticmethod
    def _extract_docx(file_path: str | Path) -> str:
        """Extract all text content from a DOCX file including headers, footers, and tables (as markdown)."""
        doc = Document(str(file_path))
        output = []

        # Headers
        for section in doc.sections:
            for hdr_ftr in [
                section.header,
                section.first_page_header,
                section.even_page_header,
            ]:
                if not hdr_ftr.is_linked_to_previous:
                    for item in hdr_ftr.iter_inner_content():
                        if isinstance(item, Paragraph):
                            if item.text.strip():
                                output.append(item.text)
                        elif isinstance(item, Table):
                            output.append(SimpleScraper._table_to_markdown(item))

        # Main body
        for item in doc.iter_inner_content():
            if isinstance(item, Paragraph):
                if item.text.strip():
                    output.append(item.text)
            elif isinstance(item, Table):
                output.append(SimpleScraper._table_to_markdown(item))

        # Footers
        for section in doc.sections:
            for hdr_ftr in [
                section.footer,
                section.first_page_footer,
                section.even_page_footer,
            ]:
                if not hdr_ftr.is_linked_to_previous:
                    for item in hdr_ftr.iter_inner_content():
                        if isinstance(item, Paragraph):
                            if item.text.strip():
                                output.append(item.text)
                        elif isinstance(item, Table):
                            output.append(SimpleScraper._table_to_markdown(item))

        return "\n\n".join(output)

    @staticmethod
    def _table_to_markdown(table: Table) -> str:
        """Convert a table to markdown format."""
        if not table.rows:
            return ""

        lines = []
        for row_idx, row in enumerate(table.rows):
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            lines.append("| " + " | ".join(cells) + " |")

            if row_idx == 0:
                lines.append("| " + " | ".join(["---"] * len(cells)) + " |")

        return "\n".join(lines)
