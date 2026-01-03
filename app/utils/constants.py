import os

CONSOLE_WIDTH = 100
EXEC_TIMEOUT = 3600
RECURSION_LIMIT = 100

CHUNK_OVERLAP = 10
CHUNK_SIZE = 50
MAX_RESULTS = 20
BATCH_SIZE = 30

LAST_N_TURNS = 20

# Vibrant unified theme built around purple accent
THEME = {
    "primary": "#a855f7",  # Vibrant purple (main accent)
    "secondary": "#ec4899",  # Vibrant pink (complementary)
    "accent": "#06b6d4",  # Vibrant cyan (tertiary)
    "success": "#10b981",  # Vibrant emerald
    "warning": "#f59e0b",  # Vibrant amber
    "error": "#ef4444",  # Vibrant red
    "muted": "#9ca3af",  # Neutral gray
    "dim": "#6b7280",  # Dim gray
    "text": "#f3f4f6",  # Light gray
    "border": "#6b21a8",  # Deep purple border
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
    "logs": (
        "%LOCALAPPDATA%\\Ally\\logs\\"
        if os.name == "nt"
        else "~/.local/share/Ally/logs/"
    ),
}


REGULAR_FILE_EXTENSIONS = [
    ".txt",
    ".md",
    ".markdown",
    ".log",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".html",
    ".csv",
]
