#!/usr/bin/env bash
# dev-setup.sh — one command to get from clone to contributing
# Usage: bash scripts/dev-setup.sh

set -e

echo "========================================="
echo " env-manager — Dev Setup"
echo "========================================="
echo ""

# ── 1. Check prerequisites ────────────────────────────

echo "--- Checking prerequisites ---"

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+ first."
    exit 1
fi

PYTHON=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python:  $PYTHON"

if ! command -v pip &>/dev/null; then
    echo "ERROR: pip not found."
    exit 1
fi

# ── 2. Create virtual environment (optional but recommended) ──

echo ""
echo "--- Creating virtual environment ---"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  Created .venv/"
else
    echo "  .venv/ already exists"
fi

source .venv/bin/activate
echo "  Activated .venv"

# ── 3. Install dependencies ────────────────────────────

echo ""
echo "--- Installing dependencies ---"

pip install --upgrade pip -q
pip install -e ".[dev]"
echo "  Python deps installed"

# ── 4. Optional: install shellcheck for bash linting ───

if ! command -v shellcheck &>/dev/null; then
    echo ""
    echo "--- Installing shellcheck (optional) ---"
    if command -v brew &>/dev/null; then
        brew install shellcheck 2>/dev/null && echo "  shellcheck installed" || echo "  shellcheck skipped (brew failed)"
    else
        echo "  shellcheck skipped (brew not found, install manually: https://shellcheck.net)"
    fi
fi

# ── 5. Verify toolchain ────────────────────────────────

echo ""
echo "--- Verifying toolchain ---"

echo "  pytest:     $(pytest --version 2>/dev/null || echo 'MISSING')"
echo "  ruff:       $(ruff --version 2>/dev/null || echo 'MISSING')"
echo "  mypy:       $(mypy --version 2>/dev/null || echo 'MISSING')"
echo "  shellcheck: $(shellcheck --version 2>/dev/null | head -1 || echo 'MISSING')"

echo ""
echo "--- Running checks ---"
make check

echo ""
echo "========================================="
echo " Dev environment ready!"
echo "========================================="
echo ""
echo " Quick start:"
echo "   make check        — run all checks (lint + typecheck + test)"
echo "   make test         — run tests only"
echo "   make lint-fix     — auto-fix lint issues"
echo "   make run-daemon   — start dashboard at http://localhost:9876"
echo "   make binary       — build standalone executable"
echo ""
echo " Or run the CLI directly:"
echo "   source .venv/bin/activate"
echo "   envs --help"
echo ""
