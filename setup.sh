#!/bin/bash
set -e

echo "=== Setting up Ally ==="

# Step 1: Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv

# Step 2: Install requirements
echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

# Step 3: Create bin/ally launcher
echo "Creating launcher script..."
CURR_DIR="$(pwd)"
mkdir -p bin
cat > bin/ally <<EOF
#!/bin/bash
source "$CURR_DIR/.venv/bin/activate"
python3 "$CURR_DIR/main.py" "\$@"
EOF
chmod +x bin/ally

# Step 4: Add bin to PATH
BIN_DIR="$CURR_DIR/bin"
SHELL_CONFIG=""

# Detect appropriate shell config file
if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    [ -f "$HOME/.bash_profile" ] && SHELL_CONFIG="$HOME/.bash_profile"
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    export PATH="$BIN_DIR:$PATH"
    if [ -n "$SHELL_CONFIG" ] && ! grep -q "$BIN_DIR" "$SHELL_CONFIG" 2>/dev/null; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_CONFIG"
        echo "Added $BIN_DIR to $SHELL_CONFIG"
        echo "Run: source $SHELL_CONFIG  (or restart your terminal)"
    else
        echo "Add this line to your shell config if needed:"
        echo "export PATH=\"$BIN_DIR:\$PATH\""
    fi
else
    echo "$BIN_DIR is already in PATH"
fi

echo "=== Setup complete! You can now run 'ally' ==="
