CONSOLE_WIDTH = 100
EXEC_TIMEOUT = 3600
RECURSION_LIMIT = 100

CHUNK_OVERLAP = 200
CHUNK_SIZE = 1000
MAX_RESULTS = 20
BATCH_SIZE = 64

LAST_N_TURNS = 20

THEME = {
    "primary": "#a855f7",
    "secondary": "#ec4899",
    "accent": "#06b6d4",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "muted": "#9ca3af",
    "dim": "#6b7280",
    "text": "#f3f4f6",
    "border": "#6b21a8",
}

PROMPTS = {
    "rag_results": "\n\nAnswer only from these documents. If irrelevant, say 'I don't know' unless user allows outside knowledge.\n",
    "continue": "Continue where you left off. Don't repeat anything already done.",
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
