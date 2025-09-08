import os

CONSOLE_WIDTH = 90
EXEC_TIMEOUT = 3600

CONTINUE_MESSAGE = "Continue where you left off. Don't repeat anything already done."

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

UI_MESSAGES = {
    "directory_prompt": "Enter project directory",
    "model_change_prompt": "Enter new {} model name",
    "continue_prompt": "Continue?",
    "change_directory": "Change working directory?",
    "project_prompt": "What would you like to build?",
    "add_context": "Add more context before code generation?",
    "continue_generation": "Continue to code generation anyway?",
    "change_models": "Change any of the current models?",
    "titles": {
        "current_directory": "Current Directory",
        "directory_updated": "Directory Updated",
        "current_models": "Current Models",
        "context_complete": "Context Engineering Complete",
        "generation_complete": "Project Generation Complete",
        "brainstormer_ready": "Brainstormer Ready",
        "codegen_ready": "CodeGen Ready",
        "generation_starting": "Starting Code Generation",
    },
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
}
