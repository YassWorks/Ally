#!/bin/bash
set -e

echo "=== Setting up Ally ==="

# script directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =========================== Step 1: Install requirements =================================

printf '\nInstalling dependencies...\n'
command -v uv >/dev/null 2>&1 || {
    echo "Error: uv not found. Please install it from https://github.com/astral-sh/uv"
    exit 1
}

cd "$INSTALL_DIR"

if [ ! -f "pyproject.toml" ]; then
    uv init >/dev/null 2>&1
fi

uv add -r requirements.txt >/dev/null 2>&1

# =========================== Step 2: Create bin/ally launcher =============================

printf '\nCreating launcher script...\n'

# wrapper script
cat > ally <<EOF
#!/bin/bash
source "$INSTALL_DIR/.venv/bin/activate"
python3 "$INSTALL_DIR/main.py" "\$@"
EOF

chmod +x ally

# =========================== Step 3: Add bin to PATH ======================================

printf '\nInstalling ally to /usr/local/bin...\n'

# check if we have permission to write to /usr/local/bin, use sudo if needed
TARGET_PATH="/usr/local/bin/ally"

if [ -w "/usr/local/bin" ]; then
    ln -sf "$INSTALL_DIR/ally" "$TARGET_PATH"
else
    echo "Sudo permissions required to install to /usr/local/bin"
    sudo ln -sf "$INSTALL_DIR/ally" "$TARGET_PATH"
fi

echo "=== Setup complete! You can now run 'ally' in a new terminal window ==="
