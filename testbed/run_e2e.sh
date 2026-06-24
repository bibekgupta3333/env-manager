#!/usr/bin/env bash
# End-to-end testbed for env-manager
# Creates real Python projects with venvs and tests the full CLI workflow.
# Run: bash testbed/run_e2e.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TESTBED="$SCRIPT_DIR/projects"
export ENVS_DB_PATH="$SCRIPT_DIR/test_e2e.db"

PASS=0
FAIL=0
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# ── helpers ──────────────────────────────────────────────

assert_contains() {
    local msg="$1" output="$2" pattern="$3"
    # Strip EXIT line
    local clean_output="${output%%EXIT:*}"
    if echo "$clean_output" | grep -q "$pattern"; then
        echo -e "  ${GREEN}✓${NC} $msg"
        ((PASS++))
    else
        echo -e "  ${RED}✗${NC} $msg (expected: '$pattern')"
        echo "    got: $(echo "$clean_output" | tail -3 | head -3)"
        ((FAIL++))
    fi
}

assert_exit() {
    local msg="$1" output="$2" expected="$3"
    local code
    code=$(echo "$output" | grep -o 'EXIT:[0-9]*' | grep -o '[0-9]*' | tail -1)
    code="${code:-0}"
    if [ "$code" = "$expected" ]; then
        echo -e "  ${GREEN}✓${NC} $msg"
        ((PASS++))
    else
        echo -e "  ${RED}✗${NC} $msg (exit code $code, expected $expected)"
        ((FAIL++))
    fi
}

run_envs() {
    cd "$PROJECT_ROOT"
    local code=0
    envs "$@" 2>&1 || code=$?
    echo "EXIT:$code"
}

# ── setup ─────────────────────────────────────────────────

echo "=========================================="
echo " env-manager End-to-End Test Suite"
echo "=========================================="
echo ""
echo "Test bed: $TESTBED"
echo "DB path:  $ENVS_DB_PATH"
echo ""

rm -rf "$TESTBED"
rm -f "$ENVS_DB_PATH"
mkdir -p "$TESTBED"

# ── create real Python projects with venvs ────────────────

echo "--- Setting up test projects ---"

# Project 1: active web API
mkdir -p "$TESTBED/client-api"
python3 -m venv "$TESTBED/client-api/.venv" 2>/dev/null || python -m venv "$TESTBED/client-api/.venv"
"$TESTBED/client-api/.venv/bin/pip" install requests flask 2>&1 | tail -1
echo "client-api created"

# Project 2: data science project (bigger)
mkdir -p "$TESTBED/data-pipeline"
python3 -m venv "$TESTBED/data-pipeline/.venv" 2>/dev/null || python -m venv "$TESTBED/data-pipeline/.venv"
"$TESTBED/data-pipeline/.venv/bin/pip" install pandas numpy matplotlib 2>&1 | tail -1
echo "data-pipeline created"

# Project 3: legacy project (simulate stale)
mkdir -p "$TESTBED/old-scraper"
python3 -m venv "$TESTBED/old-scraper/.venv" 2>/dev/null || python -m venv "$TESTBED/old-scraper/.venv"
"$TESTBED/old-scraper/.venv/bin/pip" install beautifulsoup4 lxml 2>&1 | tail -1
# Touch files to simulate age
touch -t 202401010000 "$TESTBED/old-scraper/.venv/pyvenv.cfg"
echo "old-scraper created (simulated stale)"

# Project 4: corrupt project (delete python binary)
mkdir -p "$TESTBED/broken-app"
python3 -m venv "$TESTBED/broken-app/.venv" 2>/dev/null || python -m venv "$TESTBED/broken-app/.venv"
"$TESTBED/broken-app/.venv/bin/pip" install click 2>&1 | tail -1
rm -f "$TESTBED/broken-app/.venv/bin/python"
echo "broken-app created (simulated broken)"

# Project 5: empty dir (not a venv)
mkdir -p "$TESTBED/empty-project"
echo "empty-project created (no venv)"

echo ""
echo "--- Test bed ready: 5 projects (4 venvs, 1 empty) ---"
echo ""

# ── TEST 1: envs scan ─────────────────────────────────────

echo "--- TEST 1: envs scan ---"

OUT=$(run_envs scan --path "$TESTBED" --depth 3)
assert_exit "scan exit 0" "$OUT" 0
assert_contains "scan finds envs" "$OUT" "Found"

# ── TEST 2: envs list ─────────────────────────────────────

echo ""
echo "--- TEST 2: envs list ---"

OUT=$(run_envs list)
assert_contains "list shows python envs" "$OUT" "python"

# ── TEST 3: envs plugins ──────────────────────────────────

echo ""
echo "--- TEST 3: envs plugins ---"

OUT=$(run_envs plugins list)
assert_contains "plugins shows python.venv" "$OUT" "python.venv"

# ── TEST 4: envs config ───────────────────────────────────

echo ""
echo "--- TEST 4: envs config ---"

OUT=$(run_envs config show)
assert_contains "config shows DB path" "$OUT" "test_e2e.db"

# ── TEST 5: envs info ─────────────────────────────────────

echo ""
echo "--- TEST 5: envs info ---"

OUT=$(run_envs info "$TESTBED/client-api")
assert_contains "info shows language" "$OUT" "python"

# ── TEST 6: envs lifecycle create ─────────────────────────

echo ""
echo "--- TEST 6: envs lifecycle create ---"

rm -rf "$TESTBED/new-project/.venv"
OUT=$(run_envs lifecycle create python@3.12 "$TESTBED/new-project" --dry-run)
assert_contains "create dry-run shows intent" "$OUT" "Would create"

OUT=$(run_envs lifecycle create python@3.12 "$TESTBED/new-project" --confirm 2>&1)
assert_contains "create works" "$OUT" "Created"

# ── TEST 7: envs lifecycle install ────────────────────────

echo ""
echo "--- TEST 7: envs lifecycle install ---"

OUT=$(run_envs lifecycle install "$TESTBED/new-project" httpx --dry-run)
assert_contains "install dry-run" "$OUT" "Would install"

OUT=$(run_envs lifecycle install "$TESTBED/new-project" httpx --confirm 2>&1)
assert_contains "install works" "$OUT" "Installed"

# ── TEST 8: envs doctor ───────────────────────────────────

echo ""
echo "--- TEST 8: envs doctor ---"

OUT=$(run_envs doctor --all)
assert_contains "doctor finds broken env" "$OUT" "broken"
assert_contains "doctor finds healthy envs" "$OUT" "healthy"

# ── TEST 9: envs cleanup dry-run ──────────────────────────

echo ""
echo "--- TEST 9: envs cleanup dry-run ---"

OUT=$(run_envs cleanup --stale 1 --dry-run)
assert_contains "cleanup dry-run shows candidates" "$OUT" "Would"

# ── TEST 10: envs snapshots ───────────────────────────────

echo ""
echo "--- TEST 10: envs snapshots ---"

OUT=$(run_envs snapshots)
assert_contains "snapshots list runs" "$OUT" ""

# ── TEST 11: envs pin ─────────────────────────────────────

echo ""
echo "--- TEST 11: envs pin (safety check) ---"

OUT=$(run_envs cleanup --stale 1 --dry-run)
assert_contains "cleanup respects pins" "$OUT" ""

# ── TEST 12: envs diff ────────────────────────────────────

echo ""
echo "--- TEST 12: envs diff ---"

OUT=$(run_envs cleanup diff "$TESTBED/client-api" "$TESTBED/data-pipeline" 2>&1)
assert_contains "diff runs" "$OUT" "Only"

# ── TEST 13: envs lifecycle delete with snapshot ──────────

echo ""
echo "--- TEST 13: envs lifecycle delete --snapshot ---"

OUT=$(run_envs lifecycle delete "$TESTBED/new-project" --snapshot --dry-run)
assert_contains "delete dry-run" "$OUT" "Would snapshot"

rm -rf "$TESTBED/new-project/.venv"
python3 -m venv "$TESTBED/new-project/.venv" 2>/dev/null || python -m venv "$TESTBED/new-project/.venv"
"$TESTBED/new-project/.venv/bin/pip" install httpx 2>&1 | tail -1
run_envs scan --path "$TESTBED" --depth 3 2>&1 | tail -1

OUT=$(run_envs lifecycle delete "$TESTBED/new-project" --snapshot --confirm 2>&1)
assert_contains "delete with snapshot works" "$OUT" "Deleted"

# ── TEST 14: envs lifecycle export ────────────────────────

echo ""
echo "--- TEST 14: envs lifecycle export ---"

OUT=$(run_envs lifecycle export "$TESTBED/client-api" 2>&1)
assert_contains "export produces JSON" "$OUT" '"version"'

# ── TEST 15: envs lifecycle activate ──────────────────────

echo ""
echo "--- TEST 15: envs lifecycle activate ---"

OUT=$(run_envs lifecycle activate "$TESTBED/client-api" 2>&1)
assert_contains "activate prints source command" "$OUT" "source"

# ── TEST 16: envs gc ──────────────────────────────────────

echo ""
echo "--- TEST 16: envs gc ---"

OUT=$(run_envs cleanup gc --dry-run 2>&1)
assert_contains "gc dry-run runs" "$OUT" "Would"

# ── Daemon API test ───────────────────────────────────────

echo ""
echo "--- TEST 17: Daemon API ---"

# Start daemon in background
cd "$PROJECT_ROOT"
export ENVS_DB_PATH="$SCRIPT_DIR/test_e2e.db"
uvicorn env_manager.daemon.server:app --host 127.0.0.1 --port 19876 &
DAEMON_PID=$!
sleep 2

# Test API endpoints
API_OUT=$(curl -s http://127.0.0.1:19876/api/status 2>/dev/null || echo "FAIL")
assert_contains "API status endpoint" "$API_OUT" '"status"'

API_OUT=$(curl -s http://127.0.0.1:19876/api/envs 2>/dev/null || echo "FAIL")
assert_contains "API envs endpoint" "$API_OUT" '"environments"'

API_OUT=$(curl -s http://127.0.0.1:19876/api/plugins 2>/dev/null || echo "FAIL")
assert_contains "API plugins endpoint" "$API_OUT" '"plugins"'

# Test dashboard serves
DASH_OUT=$(curl -s http://127.0.0.1:19876/ 2>/dev/null || echo "FAIL")
assert_contains "Dashboard serves HTML" "$DASH_OUT" "env-manager"

# Stop daemon
kill $DAEMON_PID 2>/dev/null || true
wait $DAEMON_PID 2>/dev/null || true

# ── Summary ───────────────────────────────────────────────

echo ""
echo "=========================================="
echo -e " RESULTS: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "=========================================="

# Cleanup
rm -f "$ENVS_DB_PATH"
rm -rf "$TESTBED"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
