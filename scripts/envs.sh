#!/usr/bin/env bash
# Run envs CLI properly (avoids the python -m freeze warning)
# Usage: bash scripts/envs.sh scan --path ~/projects

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Use the installed entry point if available, fall back to module
if command -v envs &>/dev/null; then
    exec envs "$@"
else
    exec python3 -c "from env_manager.cli.main import main; main()" "$@"
fi
