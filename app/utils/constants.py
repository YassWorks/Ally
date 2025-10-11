import os

CONSOLE_WIDTH = 90
EXEC_TIMEOUT = 3600
RECURSION_LIMIT = 100
CHUNK_OVERLAP = 200
CHUNK_SIZE = 1000

LAST_N_TURNS = 20

THEME = {
    "primary": "#4566db",
    "secondary": "#9c79ee",
    "accent": "#88c5d0",
    "success": "#10b981",
    "warning": "#ebac40",
    "error": "#ef4444",
    "muted": "#6b7280",
    "text": "#f8fafc",
    "border": "#374151",
}

PROMPTS = {
    "rag_results": "\n\nAnswer only from these documents. If irrelevant, say 'I don't know' unless user allows outside knowledge.\n",
    "continue": "Continue where you left off. Don't repeat anything already done.",
}

DEFAULT_PATHS = {
    "history": (
        "%LOCALAPPDATA%\\Ally\\history\\"
        if os.name == "nt"
        else "~/.local/share/Ally/history/"
    ),
    "database": (
        "%LOCALAPPDATA%\\Ally\\database\\"
        if os.name == "nt"
        else "~/.local/share/Ally/database/"
    ),
    "embedding_models": (
        "%LOCALAPPDATA%\\Ally\\embedding_models\\"
        if os.name == "nt"
        else "~/.local/share/Ally/embedding_models/"
    ),
    "parsing_models": (
        "%LOCALAPPDATA%\\Ally\\parsing_models\\"
        if os.name == "nt"
        else "~/.local/share/Ally/parsing_models/"
    ),
}

REGULAR_FILE_EXTENSIONS = [  # TODO: make special loading functions for json, xml, yaml
    ".txt",
    ".md",
    ".markdown",
    ".log",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
]
