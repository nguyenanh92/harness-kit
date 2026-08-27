#!/bin/sh
# install.sh — Add an agent harness to your project.
# Run from your project root:
#   curl -fsSL https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.sh | sh
#
# Optional flags passed through to the scaffold script:
#   --agent-file CLAUDE.md   (default: AGENTS.md)
#   --force                  (overwrite existing files)
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

# ── Clone + scaffold ─────────────────────────────────────────────────────────
echo "harness-kit: installing into $(pwd) ..."
git clone --depth 1 --quiet "$REPO" "$TMP/harness-kit"

"$PY" "$TMP/harness-kit/skills/scripts/scaffold_harness.py" \
    --target "$(pwd)" \
    --governance-only \
    "$@"

echo ""
echo "Done. Edit AGENTS.md (or CLAUDE.md) to customize rules for your project."
echo "Supported tools: Claude Code, Cursor, Codex, Windsurf, and any AI that reads your instruction file."
