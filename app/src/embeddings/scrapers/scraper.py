from app.src.core.ui import default_ui
from app.utils.constants import DEFAULT_PATHS
from app.src.helpers.valid_dir import validate_dir_name
import hashlib
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.datamodel.pipeline_options import smolvlm_picture_description
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.utils.model_downloader import download_models
import datetime
import sys
import os


_SETUP_COMPLETED = False


# configure parsing models path
ARTIFACTS_PATH = ""
if "ALLY_PARSING_MODELS_DIR" in os.environ:
    ARTIFACTS_PATH = Path(os.getenv("ALLY_PARSING_MODELS_DIR"))
    if not validate_dir_name(str(ARTIFACTS_PATH)):
        ARTIFACTS_PATH = ""
        default_ui.warning(
            "Invalid directory path found in $ALLY_PARSING_MODELS_DIR. Reverting to default path."
        )

if not ARTIFACTS_PATH:
    ARTIFACTS_PATH = DEFAULT_PATHS["parsing_models"]
    if os.name == "nt":
        ARTIFACTS_PATH = Path(os.path.expandvars(ARTIFACTS_PATH))
    else:
        ARTIFACTS_PATH = Path(os.path.expanduser(ARTIFACTS_PATH))


def _setup(path: str = ARTIFACTS_PATH) -> None:
    global _SETUP_COMPLETED
    try:
        with default_ui.console.status("Downloading parsing models..."):
            download_models(
                output_dir=path,
                progress=False,
                with_smolvlm=True,
            )
    except:
        print("ERROR")
        default_ui.error(
            "Failed to download Docling models used for documents parsing. Aborting..."
        )
        sys.exit(1)
    _SETUP_COMPLETED = True


def _get_hash(file_path: str) -> str:
    """Generate SHA-256 hash of a file."""

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):  # Read in 4KB chunks
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def scrape_file(file_path: str):
    """Extract text and metadata from a PDF file."""

    global _SETUP_COMPLETED
    if not _SETUP_COMPLETED:
        _setup()
    
    pipeline_options: PdfPipelineOptions = PdfPipelineOptions(
        artifacts_path=ARTIFACTS_PATH, do_ocr=True, ocr_options=EasyOcrOptions(force_full_page_ocr=True)
    )

    pipeline_options.do_formula_enrichment = True
    pipeline_options.do_code_enrichment = True
    pipeline_options.table_structure_options.do_cell_matching = False

    pipeline_options.do_picture_description = True
    pipeline_options.picture_description_options = smolvlm_picture_description

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    try:
        doc = doc_converter.convert(file_path).document
    except Exception:
        raise

    return {
        "content": doc.export_to_markdown(),
        "metadata": {
            "file_path": Path(file_path).as_posix(),
            "mod_date": datetime.datetime.fromtimestamp(
                Path(file_path).stat().st_mtime
            ).isoformat(),
            "hash": _get_hash(file_path),
        },
    }
