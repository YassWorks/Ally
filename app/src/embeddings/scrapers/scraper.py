from app.src.core.ui import default_ui
from app.utils.constants import DEFAULT_PATHS, REGULAR_FILE_EXTENSIONS
from app.src.helpers.valid_dir import validate_dir_name
from app.src.embeddings.rag_errors import SetupFailedError, ScrapingFailedError
import hashlib
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.datamodel.pipeline_options import smolvlm_picture_description
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.utils.model_downloader import download_models
from charset_normalizer import from_path
import datetime
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
    except Exception as e:
        default_ui.error(
            f"Failed to download parsing models: {e}"
        )
        raise
    _SETUP_COMPLETED = True


def get_hash(file_path: str) -> str:
    """Generate SHA-256 hash of a file."""

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):  # Read in 4KB chunks
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def _read_regular_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        return str(from_path(file_path).best())


def scrape_file(file_path: str):
    """Extract text and metadata from a PDF file."""
    
    if any(file_path.lower().endswith(x) for x in REGULAR_FILE_EXTENSIONS):
        content = _read_regular_file(file_path)
        return {
            "content": content,
            "metadata": {
                "file_path": Path(file_path).as_posix(),
                "mod_date": datetime.datetime.fromtimestamp(
                    Path(file_path).stat().st_mtime
                ).isoformat(),
                "hash": get_hash(file_path),
            },
        }

    global _SETUP_COMPLETED
    if not _SETUP_COMPLETED:
        try:
            _setup()
        except:
            raise SetupFailedError()

    pipeline_options: PdfPipelineOptions = PdfPipelineOptions(
        artifacts_path=ARTIFACTS_PATH,
        do_ocr=True,
        ocr_options=EasyOcrOptions(force_full_page_ocr=True),
    )

    pipeline_options.do_formula_enrichment = True
    pipeline_options.do_code_enrichment = True

    pipeline_options.do_picture_description = True
    pipeline_options.picture_description_options = smolvlm_picture_description

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    try:
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
            "hash": get_hash(file_path),
        },
    }
