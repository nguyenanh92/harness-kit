#!/usr/bin/env bash
set -e

echo "[init] verifying workspace (build, lint, compile, test)..."

HARNESS_DIR="harness"

# Static check: compile harness modules if present.
if [ -d "$HARNESS_DIR" ]; then
    python3 -m compileall -q "$HARNESS_DIR"
fi

# Test stage: pytest if available, else unittest discover.
if [ -d "tests" ]; then
    if command -v pytest >/dev/null 2>&1; then
        pytest -q
    else
        python3 -m unittest discover -s tests -v
    fi
else
    echo "[init] no tests/ directory yet - skipping test stage"
fi

echo "[init] OK - workspace is clean and restartable"
