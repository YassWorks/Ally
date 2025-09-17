from langchain_community.document_loaders import PyMuPDFLoader
import hashlib


def get_hash(file_path: str) -> str:
    """Generate SHA-256 hash of a file."""
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):  # Read in 4KB chunks
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_str_content(file_path: str) -> dict[str, str]:
    """Extract text and metadata from a PDF file."""
    
    loader = PyMuPDFLoader(file_path)
    data = loader.load()

    return {
        "content": " ".join([page.page_content for page in data]),
        "metadata": {
            "file_path": data[0].metadata["file_path"],
            "mod_date": data[0].metadata["moddate"],
            "hash": get_hash(file_path),
        },
    }
