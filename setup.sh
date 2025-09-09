#!/bin/bash
set -e

echo "=== Setting up Ally ==="

# =========================== Step 1: Create virtual environment ===========================

echo "Creating virtual environment..."
python3 -m venv .venv

# =========================== Step 2: Install requirements =================================

echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

# =========================== Step 3: Create bin/ally launcher =============================

echo "Creating launcher script..."
CURR_DIR="$(pwd)"
mkdir -p bin
cat > bin/ally <<EOF
#!/bin/bash
source "$CURR_DIR/.venv/bin/activate"
python3 "$CURR_DIR/main.py" "\$@"
EOF
chmod +x bin/ally

# =========================== Step 4: Add bin to PATH ======================================

BIN_DIR="$CURR_DIR/bin"
SHELL_CONFIG=""

# detect parent shell from environment
PARENT_SHELL=$(ps -p $PPID -o comm= 2>/dev/null || echo "")

if [[ "$PARENT_SHELL" == *"zsh"* ]] || [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [[ "$PARENT_SHELL" == *"bash"* ]] || [[ "$SHELL" == *"bash"* ]]; then
    if [ -f "$HOME/.bash_profile" ]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    else
        SHELL_CONFIG="$HOME/.bashrc"
    fi
else
    SHELL_CONFIG=""
fi

# check PATH membership
if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
    echo "$BIN_DIR already in PATH"
else
    if [ -n "$SHELL_CONFIG" ] && ! grep -Fxq "export PATH=\"$BIN_DIR:\$PATH\"" "$SHELL_CONFIG" 2>/dev/null; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_CONFIG"
        echo "Added $BIN_DIR to $SHELL_CONFIG"
        echo "Run: source $SHELL_CONFIG  (or restart your terminal)"
    fi
fi

echo "\nAdd this line to your shell config if needed: export PATH=\"$BIN_DIR:\$PATH\""
echo "=== Setup complete! You can now run 'ally' ==="
