#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

target="."
if [[ "${1:-}" == "--hf" ]]; then
    target=".[hf]"
fi

echo "Installing Ally..."
uv tool install --force --editable --compile-bytecode "$target"
uv tool update-shell >/dev/null 2>&1 || true

echo "Done. Open a new terminal and run: ally"
