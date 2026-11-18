import subprocess
import sys

import pymupdf
from docx import Document

from app.src.embeddings.scrapers.simple_scraper import SimpleScraper


def test_docx_text_includes_header_body_table_and_footer(tmp_path):
    doc = Document()
    doc.sections[0].header.paragraphs[0].text = "Quarterly report"
    doc.add_paragraph("Revenue grew.")
    table = doc.add_table(rows=2, cols=2)
    for cell, text in zip(
        table._cells, ["Fruit", "Color", "Apple", "Red"], strict=True
    ):
        cell.text = text
    doc.sections[0].footer.paragraphs[0].text = "Page 1"
    path = tmp_path / "report.docx"
    doc.save(path)

    content = SimpleScraper().scrape(path)["content"]

    assert content == (
        "Quarterly report\n\n"
        "Revenue grew.\n\n"
        "| Fruit | Color |\n| --- | --- |\n| Apple | Red |\n\n"
        "Page 1"
    )


def test_pdf_text_is_extracted(tmp_path):
    pdf = pymupdf.open()
    pdf.new_page().insert_text((72, 72), "The secret word is pineapple.")
    path = tmp_path / "notes.pdf"
    pdf.save(path)

    result = SimpleScraper().scrape(path)

    assert "pineapple" in result["content"]
    assert result["metadata"]["file_path"] == path.as_posix()


def test_parsers_load_only_when_needed(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("plain text", encoding="utf-8")
    code = (
        "import sys\n"
        "from app.src.embeddings.scrapers.simple_scraper import SimpleScraper\n"
        f"print(SimpleScraper().scrape({str(path)!r})['content'])\n"
        "print(sorted({'docx', 'pymupdf', 'pymupdf4llm'} & set(sys.modules)))\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )

    assert result.stdout.splitlines() == ["plain text", "[]"]
