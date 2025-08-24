import os

def validate_dir_name(path: str) -> bool:
    """Return True if dir name is valid for current OS."""
    
    basename = os.path.basename(path.rstrip(os.sep))  # strip trailing slash
    # Windows
    if os.name == "nt":  
        invalid_chars = '<>:"/\\|?*'
        
    # POSIX
    else:  
        invalid_chars = '\0'
        
    return not any(c in basename for c in invalid_chars)