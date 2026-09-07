#!/bin/sh
# install.sh — Add an agent harness to your project.
# Run from your project root:
#   curl -fsSL https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.sh | sh
#
# Flags (passed before the pipe, via -s --):
#   --full               Also scaffold the Python runtime (harness/ dir + 7 modules)
#   --agent-file CLAUDE.md   (default: AGENTS.md)
#   --force              Overwrite existing files
#
# Default is governance-only (5 files, works for any language/stack).
# Use --full for Python-based orchestration or programmatic agent loops.
set -e

REPO="https://github.com/nguyenanh92/harness-kit.git"
TMP=$(mktemp -d)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# ── Python ──────────────────────────────────────────────────────────────────
PY=""
for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        if "$cmd" -c "import sys; sys.exit(0 if sys.version_info>=(3,8) else 1)" 2>/dev/null; then
            PY="$cmd"
            break
        fi
    fi
done
if [ -z "$PY" ]; then
    echo "Error: Python 3.8+ is required. Install it from https://python.org" >&2
    exit 1
fi

# ── Git ──────────────────────────────────────────────────────────────────────
if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is required. Install it from https://git-scm.com" >&2
    exit 1
fi

# ── Parse --full flag (consumed here, not forwarded to scaffold) ──────────────
GOVERNANCE_ONLY="--governance-only"
PASSTHROUGH=""
for arg in "$@"; do
    if [ "$arg" = "--full" ]; then
        GOVERNANCE_ONLY=""
    else
        PASSTHROUGH="$PASSTHROUGH $arg"
    fi
done

# ── Clone + scaffold ─────────────────────────────────────────────────────────
echo "harness-kit: installing into $(pwd) ..."
git clone --depth 1 --quiet "$REPO" "$TMP/harness-kit"

# shellcheck disable=SC2086
"$PY" "$TMP/harness-kit/skills/scripts/scaffold_harness.py" \
    --target "$(pwd)" \
    $GOVERNANCE_ONLY \
    $PASSTHROUGH

