from langchain_core.tools import tool
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from rapidfuzz import fuzz


IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".gradle",
    ".maven",
    ".next",
    ".nuxt",
    ".nyc_output",
    ".pytest_cache",
    ".tox",
    ".mypy_cache",
    ".cache",
    ".tmp",
    ".temp",
    "logs",
    "log",
    ".DS_Store",
    ".env",
    ".env.local",
}
MAX_FILE_SIZE_BYTES = 1_000_000  # 1 mb
MAX_RESULTS = 30


@tool
def find_references(dir_path: str, query: str) -> str:
    """
    ## PRIMARY PURPOSE:
    Quickly locate file references to an exact keyword or a close match within a directory tree.

    ## WHEN TO USE:
    - You need exact occurrences of an identifier, phrase, config key, or string
    - If no exact hits are found, automatically surface close matches

    ## PARAMETERS:
        dir_path (str): Root directory to search
        query (str): Exact keyword or phrase to find

    ## RETURNS:
        str: path:line: snippet
    """

    try:
        if not os.path.isdir(dir_path):
            return f"Not a directory: {dir_path}"

        files = _collect_files(dir_path)
        if not files:
            return "No readable text files found"

        results = _search_exact(files, query)

        if not results:
            results = _search_fuzzy(files, query)

        if not results:
            return f"No matches for: {query}"

        out_lines = []
        for fp, ln, snip in results:
            out_lines.append(f"{fp}:{ln}: {snip}")

        return "\n".join(out_lines)

    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def find_declaration(dir_path: str, symbol: str) -> str:
    """
    ## PRIMARY PURPOSE:
    Locate probable declarations/definitions of a symbol in a directory tree.

    ## WHEN TO USE:
    - You need where a function, class, variable, or type is defined

    ## PARAMETERS:
        dir_path (str): Root directory to search
        symbol (str): Identifier to find declarations for

    ## RETURNS:
        str: path:line: snippet
    """
    try:
        if not os.path.isdir(dir_path):
            return f"Not a directory: {dir_path}"

        files = _collect_files(dir_path)
        if not files:
            return "No readable text files found"

        decls = _search_declarations(files, symbol)
        if not decls:
            return f"No declarations for: {symbol}"

        out_lines = []
        for fp, ln, snip in decls:
            out_lines.append(f"{fp}:{ln}: {snip}")

        return "\n".join(out_lines)
    except Exception as e:
        return f"Search error: {str(e)}"


def _is_text_file(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:  # lazy but works
            f.read(1024)
        return True
    except Exception:
        return False


def _trim_snippet(
    line: str, match_start: int | None, match_len: int, width: int = 100
) -> str:
    line = line.rstrip("\n\r")
    if match_start is None:
        snippet = line.strip()
        return snippet[:width]
    half = max(0, (width - match_len) // 2)
    start = max(0, match_start - half)
    end = min(len(line), match_start + match_len + half)
    snippet = line[start:end].strip()
    snippet = re.sub(r"\s+", " ", snippet)
    return snippet


def _collect_files(root: str) -> list[str]:
    files: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored dirs immediately
        dirnames[:] = [
            d for d in dirnames 
            if not any(re.search(rf'^{re.escape(pattern)}', d) for pattern in IGNORED_DIRS)
        ]

        for entry in filenames:
            fp = os.path.join(dirpath, entry)
            try:
                stat = os.stat(fp)
                if stat.st_size > MAX_FILE_SIZE_BYTES:
                    continue
            except OSError:
                continue

            if _is_text_file(fp):
                files.append(fp)

    return files


def _search_exact(files: list[str], query: str) -> list[tuple[str, int, str]]:
    ql = query.lower()
    results: list[tuple[str, int, str]] = []
    res_lock = threading.Lock()
    stop_event = threading.Event()
    file_order = {fp: idx for idx, fp in enumerate(files)}

    def scan_file(fp: str) -> None:
        if stop_event.is_set():
            return
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    if stop_event.is_set():
                        break
                    ll = line.lower()
                    pos = ll.find(ql)
                    if pos != -1:
                        snippet = _trim_snippet(line, pos, len(query))
                        with res_lock:
                            if not stop_event.is_set():
                                results.append((fp, i, snippet))
                                if len(results) >= MAX_RESULTS:
                                    stop_event.set()
                                    break
        except Exception:
            # skip unreadable file
            return

    with ThreadPoolExecutor() as ex:
        for fp in files:
            ex.submit(scan_file, fp)

    # deterministic-ish ordering by original file order then line number
    results.sort(key=lambda t: (file_order.get(t[0], 0), t[1]))
    return results[:MAX_RESULTS]


def _search_fuzzy(files: list[str], query: str) -> list[tuple[str, int, str]]:
    query_l = query.lower()
    token_re = re.compile(r"[A-Za-z0-9_./-]{2,}")
    results: list[tuple[str, int, str]] = []
    res_lock = threading.Lock()
    stop_event = threading.Event()
    file_order = {fp: idx for idx, fp in enumerate(files)}

    def scan_file(fp: str) -> None:
        if stop_event.is_set():
            return
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    if stop_event.is_set():
                        break
                    ll = line.lower()
                    for token in token_re.findall(line):
                        if stop_event.is_set():
                            break
                        token_l = token.lower()
                        if fuzz.partial_ratio(query_l, token_l) >= 75:
                            snippet = _trim_snippet(line, ll.find(token_l), len(token))
                            with res_lock:
                                if not stop_event.is_set():
                                    results.append((fp, i, snippet))
                                    if len(results) >= MAX_RESULTS:
                                        stop_event.set()
                                        break
        except OSError:
            return

    with ThreadPoolExecutor() as ex:
        for fp in files:
            ex.submit(scan_file, fp)

    results.sort(key=lambda t: (file_order.get(t[0], 0), t[1]))
    return results[:MAX_RESULTS]


def _search_declarations(files: list[str], name: str) -> list[tuple[str, int, str]]:
    nq = re.escape(name)
    patterns = [
        rf"\bdef\s+{nq}\b",  # Python function
        rf"\bclass\s+{nq}\b",  # Python/JS/TS class
        rf"\b{nq}\s*=\s*",  # variable/const assignment
        rf"\bfrom\s+[^\n]+\bimport\b[^\n]*\b{nq}\b",  # from x import name
        rf"\bimport\s+[^\n]*\b{nq}\b",  # import name
        rf"\bfunction\s+{nq}\b",  # JS function
        rf"\b(?:const|let|var)\s+{nq}\b",  # JS variable
        rf"\bexport\s+(?:function|class|const|let|var|type|interface|enum)\s+{nq}\b",  # TS export decls
        rf"\btype\s+{nq}\b",  # TS/Flow type
        rf"\binterface\s+{nq}\b",  # TS interface
        rf"\benum\s+{nq}\b",  # TS/others enum
        rf"\bstruct\s+{nq}\b",  # C/Go/Rust struct
        rf"\bfn\s+{nq}\b",  # Rust function
    ]
    regex = re.compile("|".join(patterns), re.IGNORECASE)

    results: list[tuple[str, int, str]] = []
    res_lock = threading.Lock()
    stop_event = threading.Event()
    file_order = {fp: idx for idx, fp in enumerate(files)}

    def scan_file(fp: str) -> None:
        if stop_event.is_set():
            return
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    if stop_event.is_set():
                        break
                    m = regex.search(line)
                    if m:
                        snippet = _trim_snippet(line, m.start(), len(m.group(0)))
                        with res_lock:
                            if not stop_event.is_set():
                                results.append((fp, i, snippet))
                                if len(results) >= MAX_RESULTS:
                                    stop_event.set()
                                    break
        except Exception:
            return

    with ThreadPoolExecutor() as ex:
        for fp in files:
            ex.submit(scan_file, fp)

    results.sort(key=lambda t: (file_order.get(t[0], 0), t[1]))
    return results[:MAX_RESULTS]


FIND_TOOLS = [
    find_references,
    find_declaration,
]
