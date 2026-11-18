import os
import re
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from langchain_core.tools import tool
from rapidfuzz import fuzz

from app.utils.logger import logger

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".gradle",
    ".maven",
    ".next",
    ".nuxt",
    ".nyc_output",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".mypy_cache",
    ".cache",
    ".tmp",
    ".temp",
    "logs",
    "log",
}
IGNORED_FILES = {".DS_Store", ".env", ".env.local"}
MAX_FILE_SIZE_BYTES = 10_000_000
MAX_RESULTS = 30
FUZZY_THRESHOLD = 75
DECLARATION_PATTERNS = [
    r"\bdef\s+{name}\b",
    r"\bclass\s+{name}\b",
    r"\b{name}\s*=\s*",
    r"\bfrom\s+[^\n]+\bimport\b[^\n]*\b{name}\b",
    r"\bimport\s+[^\n]*\b{name}\b",
    r"\bfunction\s+{name}\b",
    r"\b(?:const|let|var)\s+{name}\b",
    r"\bexport\s+(?:function|class|const|let|var|type|interface|enum)\s+{name}\b",
    r"\btype\s+{name}\b",
    r"\binterface\s+{name}\b",
    r"\benum\s+{name}\b",
    r"\bstruct\s+{name}\b",
    r"\bfn\s+{name}\b",
]

Match = tuple[int, int]
Hit = tuple[str, int, str]


@tool(parse_docstring=True)
def find_references(dir_path: str, query: str) -> str:
    """Search the files under a directory for lines that contain a keyword.

    The search ignores case. When nothing matches exactly, lines with close
    matches are returned instead. Returns up to 30 lines formatted as
    path:line: snippet.

    Args:
        dir_path: Directory to search recursively.
        query: Keyword or phrase to look for.
    """
    try:
        if not os.path.isdir(dir_path):
            return f"Not a directory: {dir_path}"

        files = _collect_files(dir_path)
        if not files:
            return "No readable text files found"

        hits = _scan(files, _exact_matcher(query)) or _scan(
            files, _fuzzy_matcher(query)
        )
        if not hits:
            return f"No matches for: {query}"
        return _format(hits)
    except Exception as e:
        logger.error(f"Error searching for {query} in {dir_path}", exc_info=e)
        return f"Search error: {e}"


@tool(parse_docstring=True)
def find_declaration(dir_path: str, symbol: str) -> str:
    """Find where a function, class, variable or type is declared.

    Recognizes common declaration forms in Python, JavaScript, TypeScript, Go,
    Rust and C. Returns up to 30 lines formatted as path:line: snippet.

    Args:
        dir_path: Directory to search recursively.
        symbol: Name of the symbol.
    """
    try:
        if not os.path.isdir(dir_path):
            return f"Not a directory: {dir_path}"

        files = _collect_files(dir_path)
        if not files:
            return "No readable text files found"

        hits = _scan(files, _declaration_matcher(symbol))
        if not hits:
            return f"No declarations for: {symbol}"
        return _format(hits)
    except Exception as e:
        logger.error(f"Error searching for {symbol} in {dir_path}", exc_info=e)
        return f"Search error: {e}"


def _collect_files(root: str) -> list[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for name in filenames:
            if name in IGNORED_FILES:
                continue
            path = os.path.join(dirpath, name)
            try:
                if os.path.getsize(path) > MAX_FILE_SIZE_BYTES:
                    continue
            except OSError:
                continue
            if _is_text_file(path):
                files.append(path)
    return files


def _is_text_file(path: str) -> bool:
    try:
        with open(path, encoding="utf-8", errors="strict") as f:
            f.read(1024)
        return True
    except Exception:
        return False


def _exact_matcher(query: str) -> Callable[[str], Match | None]:
    needle = query.lower()

    def match(line: str) -> Match | None:
        start = line.lower().find(needle)
        return (start, len(needle)) if start != -1 else None

    return match


def _fuzzy_matcher(query: str) -> Callable[[str], Match | None]:
    needle = query.lower()
    token = re.compile(r"[A-Za-z0-9_./-]{2,}")

    def match(line: str) -> Match | None:
        for found in token.finditer(line):
            if fuzz.partial_ratio(needle, found.group(0).lower()) >= FUZZY_THRESHOLD:
                return found.start(), len(found.group(0))
        return None

    return match


def _declaration_matcher(name: str) -> Callable[[str], Match | None]:
    escaped = re.escape(name)
    regex = re.compile(
        "|".join(p.format(name=escaped) for p in DECLARATION_PATTERNS), re.IGNORECASE
    )

    def match(line: str) -> Match | None:
        found = regex.search(line)
        return (found.start(), len(found.group(0))) if found else None

    return match


def _scan(files: list[str], match: Callable[[str], Match | None]) -> list[Hit]:
    hits: list[Hit] = []
    lock = threading.Lock()
    full = threading.Event()

    def scan_file(path: str) -> None:
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for number, line in enumerate(f, start=1):
                    if full.is_set():
                        return
                    found = match(line)
                    if found is None:
                        continue
                    with lock:
                        if len(hits) >= MAX_RESULTS:
                            full.set()
                            return
                        hits.append((path, number, _snippet(line, *found)))
        except OSError:
            return

    with ThreadPoolExecutor() as pool:
        list(pool.map(scan_file, files))

    order = {path: index for index, path in enumerate(files)}
    hits.sort(key=lambda hit: (order[hit[0]], hit[1]))
    return hits


def _snippet(line: str, start: int, length: int, width: int = 100) -> str:
    line = line.rstrip("\r\n")
    half = max(0, (width - length) // 2)
    snippet = line[max(0, start - half) : start + length + half].strip()
    return re.sub(r"\s+", " ", snippet)


def _format(hits: list[Hit]) -> str:
    return "\n".join(f"{path}:{number}: {snippet}" for path, number, snippet in hits)


FIND_TOOLS = [
    find_references,
    find_declaration,
]
