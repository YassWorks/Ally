from app.src.core.ui import default_ui
from app.src.embeddings.scrapers.docling_setup import ARTIFACTS_PATH, setup
from app.src.embeddings.scrapers.abstract_scraper import Scraper
from app.utils.constants import REGULAR_FILE_EXTENSIONS
from app.src.embeddings.rag_errors import SetupFailedError, ScrapingFailedError
from pathlib import Path
import datetime


_DOCLING_SETUP_COMPLETED = False
_RETRIED_DOCLING_SETUP = False


class DoclingScraper(Scraper):

    def scrape(self, file_path: str | Path) -> dict:
        """Extract text and metadata from a file using Docling."""

        global _DOCLING_SETUP_COMPLETED
        if not _DOCLING_SETUP_COMPLETED:
            try:
                setup(path=ARTIFACTS_PATH)
                _DOCLING_SETUP_COMPLETED = True
            except:
                raise SetupFailedError()

        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            EasyOcrOptions,
        )
        from docling.datamodel.pipeline_options import smolvlm_picture_description
        from docling.document_converter import (
            PdfFormatOption,
            ImageFormatOption,
            WordFormatOption,
        )

        if any(file_path.lower().endswith(x) for x in REGULAR_FILE_EXTENSIONS):
            content = self.read_regular_file(file_path)
            return {
                "content": content,
                "metadata": {
                    "file_path": Path(file_path).as_posix(),
                    "mod_date": datetime.datetime.fromtimestamp(
                        Path(file_path).stat().st_mtime
                    ).isoformat(),
                    "hash": self.get_hash(file_path),
                },
            }

        pipeline_options = PdfPipelineOptions(
            artifacts_path=ARTIFACTS_PATH,
            do_ocr=True,
            ocr_options=EasyOcrOptions(force_full_page_ocr=True),
        )

        pipeline_options.do_table_structure = True
        pipeline_options.do_formula_enrichment = True
        pipeline_options.do_code_enrichment = True
        pipeline_options.do_picture_description = True
        pipeline_options.generate_picture_images = True

        pipeline_options.picture_description_options = smolvlm_picture_description

        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
                InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
                InputFormat.DOCX: WordFormatOption(pipeline_options=pipeline_options),
            }
        )

        try:
            with default_ui.console.status(f"Scraping '{file_path}'..."):
                doc = doc_converter.convert(file_path).document
        except:
            # trying to redownload models ONCE if first scraping fails
            global _RETRIED_DOCLING_SETUP
            if _RETRIED_DOCLING_SETUP:
                raise ScrapingFailedError()

            default_ui.warning(
                "Scraping failed. Attempting to redownload parsing models and retry..."
            )
            
            _RETRIED_DOCLING_SETUP = True
            try:
                setup(path=ARTIFACTS_PATH)
            except:
                raise SetupFailedError()

            try:
                with default_ui.console.status(f"Scraping '{file_path}'..."):
                    doc = doc_converter.convert(file_path).document
            except:
                raise ScrapingFailedError()

        return {
            "content": doc.export_to_markdown(),
            "metadata": {
                "file_path": Path(file_path).as_posix(),
                "mod_date": datetime.datetime.fromtimestamp(
                    Path(file_path).stat().st_mtime
                ).isoformat(),
                "hash": self.get_hash(file_path),
            },
        }
