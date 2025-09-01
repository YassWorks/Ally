from langchain_core.tools import tool
import os
import re
from difflib import get_close_matches
from typing import List, Tuple


IGNORED_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".idea", ".vscode"}
MAX_FILE_SIZE_BYTES = 1_000_000  # 1 mb
MAX_RESULTS = 50


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

        exact = _search_exact(files, query)
        results = exact

        if not results:
            fuzzy = _search_fuzzy(files, query)
            results = fuzzy

        if not results:
            return f"No matches for: {query}"

        out_lines = []
        for fp, ln, snip in results:
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


def _collect_files(root: str) -> List[str]:
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored dirs in-place for performance
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for name in filenames:
            fp = os.path.join(dirpath, name)
            try:
                if os.path.getsize(fp) > MAX_FILE_SIZE_BYTES:
                    continue
            except OSError:
                continue
            if _is_text_file(fp):
                files.append(fp)
    return files


def _search_exact(files: List[str], query: str) -> List[Tuple[str, int, str]]:
    ql = query.lower()
    results: List[Tuple[str, int, str]] = []
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    ll = line.lower()
                    pos = ll.find(ql)
                    if pos != -1:
                        snippet = _trim_snippet(line, pos, len(query))
                        results.append((fp, i, snippet))
                        if len(results) >= MAX_RESULTS:
                            return results
        except Exception:
            # skip unreadable file
            continue
    return results


def _search_fuzzy(files: List[str], query: str) -> List[Tuple[str, int, str]]:
    # Build a small vocabulary of tokens to compare against the query
    vocab: List[str] = []
    token_re = re.compile(r"[A-Za-z0-9_./-]{3,}")
    seen = set()
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                for _ in range(200):  # sample first ~200 lines per file to keep it fast
                    line = f.readline()
                    if not line:
                        break
                    for t in token_re.findall(line):
                        tl = t.lower()
                        if tl not in seen:
                            seen.add(tl)
                            vocab.append(tl)
                            if len(vocab) >= 5000:
                                break
                    if len(vocab) >= 5000:
                        break
        except Exception:
            continue
        if len(vocab) >= 5000:
            break

    close = set(get_close_matches(query.lower(), vocab, n=12, cutoff=0.78))
    if not close:
        return []

    # Find lines that contain any of the close tokens
    results: List[Tuple[str, int, str]] = []
    pattern = re.compile(
        "|".join(map(re.escape, sorted(close, key=len, reverse=True))), re.IGNORECASE
    )
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    m = pattern.search(line)
                    if m:
                        snippet = _trim_snippet(line, m.start(), len(m.group(0)))
                        results.append((fp, i, snippet))
                        if len(results) >= MAX_RESULTS:
                            return results
        except Exception:
            continue
    return results


FIND_TOOLS = [
    find_references,
]
