from app.src.embeddings.rag_errors import ScrapingFailedError
from charset_normalizer import from_path
from abc import ABC, abstractmethod
from pathlib import Path


class Scraper(ABC):

    @abstractmethod
    def scrape(self, path: str | Path) -> dict:
        """Scrape content from the given file path.

        Args:
            path (str | Path): The path to scrape.

        Returns:
            dict: The scraped content and metadata.
            
            **format**:
            {
                "content": str,
                "metadata": {
                    "file_path": str,
                    "mod_date": str,
                    "hash": str,
                },
            }
        """
        pass

    @staticmethod
    def get_hash(file_path: str | Path) -> str:
        """Generate SHA-256 hash of a file."""
        import hashlib

        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):  # Read in 4KB chunks
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    @staticmethod
    def _read_json_file(file_path: str | Path) -> str:
        """Load and format JSON file with proper structure."""
        import json

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return json.dumps(data, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return str(from_path(file_path).best())

    @staticmethod
    def _read_xml_file(file_path: str | Path) -> str:
        """Load and format XML file with proper structure."""
        import xml.etree.ElementTree as ET

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            def xml_to_text(element, level=0) -> str:
                """Convert XML element to formatted text representation."""
                indent = "  " * level
                text = f"{indent}<{element.tag}"

                if element.attrib:
                    attrs = " ".join(f'{k}="{v}"' for k, v in element.attrib.items())
                    text += f" {attrs}"
                text += ">"

                if element.text and element.text.strip():
                    text += f"\n{indent}  {element.text.strip()}"

                if len(element):
                    text += "\n"
                    for child in element:
                        text += xml_to_text(child, level + 1) + "\n"
                    text += f"{indent}"

                text += f"</{element.tag}>"
                return text

            return xml_to_text(root)
        except (ET.ParseError, UnicodeDecodeError):
            return str(from_path(file_path).best())

    @staticmethod
    def _read_yaml_file(file_path: str | Path) -> str:
        """Load and format YAML file with proper structure."""
        import yaml

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return yaml.dump(
                    data, default_flow_style=False, allow_unicode=True, sort_keys=False
                )
        except (yaml.YAMLError, UnicodeDecodeError):
            return str(from_path(file_path).best())

    @staticmethod
    def read_regular_file(file_path: str | Path) -> str:
        """Read and format file based on its extension."""
        file_lower = str(file_path).lower()

        try:
            if file_lower.endswith(".json"):
                return Scraper._read_json_file(file_path)

            elif file_lower.endswith(".xml"):
                return Scraper._read_xml_file(file_path)

            elif file_lower.endswith((".yaml", ".yml")):
                return Scraper._read_yaml_file(file_path)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            
            except UnicodeDecodeError:
                return str(from_path(file_path).best())
        
        except Exception as e:
            raise ScrapingFailedError(f"Failed to read file: {e}")
