
UI_MESSAGES = {
    # Prompts
    "directory_prompt": "Enter project directory",
    "model_change_prompt": "Enter new {} model name",
    "continue_prompt": "Continue?",
    "change_directory": "Change working directory?",
    "project_prompt": "What would you like to build?",
    "add_context": "Add more context before code generation?",
    "continue_generation": "Continue to code generation anyway?",
    "change_models": "Change any of the current models?",
    
    # Titles
    "titles": {
        "current_directory": "Current Directory",
        "directory_updated": "Directory Updated",
        "current_models": "Current Models",
        "context_complete": "Context Engineering Complete",
        "generation_complete": "Project Generation Complete",
        "brainstormer_ready": "Brainstormer Ready",
        "codegen_ready": "CodeGen Ready",
        "generation_starting": "Starting Code Generation",
        "goodbye": "Goodbye",
        "history_cleared": "History Cleared",
        "interrupted": "Interrupted",
        "extended_session": "Extended Session",
        "warning": "Warning",
        "error": "Error",
        "help": "Help",
        "tool_executing": "Tool Executing",
        "assistant": "Assistant",
        "continuing_session": "Continuing Session",
        "current_session_id": "Current Session ID",
        "latest_references": "Latest References",
        "current_model": "Current Model",
        "change_model": "Change Model",
        "rag_enabled": "RAG Enabled",
        "rag_disabled": "RAG Disabled",
        "info": "Info",
        "collections": "Collections",
        "collection_deleted": "Collection Deleted",
        "database_reset": "Database Reset",
    },
    
    # Messages
    "messages": {
        "goodbye": "Thanks for using Ally!",
        "history_cleared": "Conversation history cleared",
        "session_interrupted": "Session interrupted by user",
        "recursion_warning": "Agent has been processing for a while.\nContinue or refine your prompt?",
        "initializing_agents": "Initializing agents...",
        "working_on_task": "Working on the task...",
        "generation_starting_detail": "The CodeGen Agent is now generating code based on the context provided.",
        "brainstormer_ready_detail": "Type '/exit' or press Ctrl+C to continue to code generation",
        "codegen_ready_detail": "Starting interactive coding session with the coding agent...",
        "continuing_session": "Resuming from previous context...",
        "no_references": "No references available.",
        "rag_enabled": "Retrieval-Augmented Generation is now active.",
        "rag_disabled": "Retrieval-Augmented Generation is now inactive.",
        "collections_header": "Collections available:",
        "collection_deleted": "Collection '{}' has been deleted.",
        "all_collections_deleted": "All collections have been deleted.",
    },
    
    # Warnings
    "warnings": {
        "failed_confirm": "Failed to confirm action. Continuing with default value ({})",
        "rag_not_available": "RAG is not available. Please configure an embedding provider.",
        "rag_enabled_no_client": "RAG is enabled but no database client is configured.",
        "rag_features_disabled": "RAG features disabled.",
        "invalid_db_path": "Invalid directory path found in $ALLY_DATABASE_DIR. Reverting to default path.",
        "recursion_limit_reached": "Agent processing took longer than expected (Max recursion limit reached)",
    },
    
    # Errors
    "errors": {
        "failed_initialize_agents": "Failed to initialize default agents: {}",
        "config_error": "Configuration error: {}",
        "failed_validate_config": "Failed to validate configuration: {}",
        "failed_setup_coding": "Failed to setup coding configuration: {}",
        "unexpected_error": "An unexpected error occurred: {}",
        "codegen_failed": "Code generation workflow failed to complete successfully",
        "invalid_directory": "Invalid directory name: {}",
        "failed_create_directory": "Failed to create directory",
        "failed_initialize_coding": "Failed to initialize coding workflow: {}",
        "workflow_execution_failed": "Workflow execution failed: {}",
        "coding_session_failed": "The interactive coding session did not exit safely",
        "failed_integrate_web_search": "Failed to integrate web search capabilities: {}",
        "rate_limit_exceeded": "Rate limit exceeded. Please try again later",
        "db_not_initialized": "Database client is not initialized. There might be an issue with your embeddings config.",
        "invalid_directory_path": "Invalid directory path: {}",
        "directory_not_exist": "Directory {} does not exist.",
        "failed_scrape": "Failed to scrape file: {}. Skipping.",
        "collection_not_exist": "Collection {} does not exist.",
        "failed_create_db_directory": "Failed to create database directory: {}",
        "failed_save_indexed": "Failed to save indexed collections: {}",
        "failed_install_packages": "Failed to install required packages. Please install them manually. Error: {}",
        "db_access_error": "Database access error occurred.",
        "setup_failed": "Setup failed.",
        "command_failed": "Command '{}' failed: {}",
        "unknown_command": "Unknown command. Type /help for instructions.",
        "specify_model": "Please specify a model to change to.",
        "unknown_model_command": "Unknown model command. Type /help for instructions.",
        "agent_execution_failed": "[ERROR] Agent execution failed.",
        "no_messages_returned": "[ERROR] Agent did not return any messages.",
    },
    
    # Confirmations
    "confirmations": {
        "continue_from_left_off": "Continue from where the agent left off?",
        "continue_anyway": "Something went wrong during the brainstorming process. Do you wish to continue anyway?",
        "delete_collection": "Are you sure you want to delete the collection '{}'?",
        "reset_database": "Are you sure you want to reset the database? This action cannot be undone.",
    },
    
    # Usage Messages
    "usage": {
        "embed": "Usage: /embed <directory_path> <collection_name>",
        "index": "Usage: /index <collection_name>",
        "unindex": "Usage: /unindex <collection_name>",
        "delete": "Usage: /delete <collection_name>",
    },
    
    # Success Messages
    "success": {
        "collection_indexed": "Collection '{}' is now indexed.",
        "collection_unindexed": "Collection '{}' is now unindexed.",
        "documents_embedded": "Documents from '{}' have been embedded into collection '{}'.",
    },
    
    # Help Content
    "help": {
        "content": [
            "Use `Ctrl+n` to enter a new line and `Enter` to submit your message.",
            "| Command | Description |",
            "|---------|-------------|",
            "| `/quit`, `/exit`, `/q` | Exit |",
            "| `/clear` | Clear history* |",
            "| `/cls` | Clear screen |",
            "| `/model (change)` | Show/change AI model |",
            "| `/project` | Start project generation workflow |",
            "| `/help`, `/h` | Show this help message |",
        ],
        "model_suffix": "Model: *{}*",
        "footer": "\n> **Not recommended during long running tasks. Use at your own risk.*",
    },
    
    # Tool Messages
    "tool": {
        "title": "## {}",
        "arguments_header": "\n**Arguments:**",
        "output_header": "**Output:**",
        "truncated": "\n... *(truncated)*",
        "tool_complete": "Tool Complete: {}",
    },
}
