import datetime
from pathlib import Path

from app.src.embeddings.rag_errors import ScrapingFailedError
from app.src.embeddings.scrapers.abstract_scraper import Scraper


class SimpleScraper(Scraper):
    """Read text, PDF and DOCX files locally, loading each parser on first use."""

    def scrape(self, file_path: str | Path) -> dict:
        """Extract the text and metadata of ``file_path``.

        Raises:
            ScrapingFailedError: If the file cannot be read.
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            kind, extract = "PDF file", _extract_pdf
        elif suffix == ".docx":
            kind, extract = "DOCX file", _extract_docx
        else:
            kind, extract = "file", self.read_regular_file

        try:
            text = extract(path)
        except Exception as e:
            raise ScrapingFailedError(f"Failed to scrape {kind}: {e}") from e

        return {
            "content": text.strip(),
            "metadata": {
                "file_path": path.as_posix(),
                "mod_date": datetime.datetime.fromtimestamp(
                    path.stat().st_mtime
                ).isoformat(),
                "hash": self.get_hash(path),
            },
        }


def _extract_pdf(path: Path) -> str:
    import pymupdf4llm

    return pymupdf4llm.to_markdown(str(path))


def _extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    headers = [
        part
        for section in doc.sections
        for part in (
            section.header,
            section.first_page_header,
            section.even_page_header,
        )
    ]
    footers = [
        part
        for section in doc.sections
        for part in (
            section.footer,
            section.first_page_footer,
            section.even_page_footer,
        )
    ]

    output = []
    for part in headers:
        if not part.is_linked_to_previous:
            output.extend(_block_texts(part))
    output.extend(_block_texts(doc))
    for part in footers:
        if not part.is_linked_to_previous:
            output.extend(_block_texts(part))
    return "\n\n".join(output)


def _block_texts(container) -> list[str]:
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    texts = []
    for item in container.iter_inner_content():
        if isinstance(item, Paragraph):
            if item.text.strip():
                texts.append(item.text)
        elif isinstance(item, Table):
            texts.append(_table_to_markdown(item))
    return texts


def _table_to_markdown(table) -> str:
    lines = []
    for index, row in enumerate(table.rows):
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        lines.append("| " + " | ".join(cells) + " |")
        if index == 0:
            lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
    return "\n".join(lines)
