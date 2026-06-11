#!/usr/bin/env bash
set -e

echo "[init] verifying workspace (build, lint, compile, test)..."

# Static check: compile Python harness modules
if ls *.py >/dev/null 2>&1; then
    python3 -m py_compile *.py
fi

# Test stage: run pytest if available, else unittest discover
if command -v pytest >/dev/null 2>&1 && [ -d "tests" ]; then
    pytest -q
elif [ -d "tests" ]; then
    python3 -m unittest discover -s tests -v
else
    echo "[init] no tests/ directory yet — skipping test stage"
fi

echo "[init] OK — workspace is clean and restartable"
