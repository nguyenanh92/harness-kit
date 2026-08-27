# install.ps1 — Add an agent harness to your project.
# Run from your project root:
#   irm https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.ps1 | iex
#
# Flags (pass as arguments when invoking directly, not via iex pipe):
#   --full               Also scaffold the Python runtime (harness\ dir + 7 modules)
#   --agent-file CLAUDE.md   (default: AGENTS.md)
#   --force              Overwrite existing files
#
# Default is governance-only (5 files, works for any language/stack).
# Use --full for Python-based orchestration or programmatic agent loops.
#
# To pass flags via pipe, use:
#   & ([ScriptBlock]::Create((irm https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.ps1))) --full
$ErrorActionPreference = 'Stop'

$repo = "https://github.com/nguyenanh92/harness-kit.git"
$tmp  = Join-Path $env:TEMP "harness-kit-$(Get-Random)"

function Find-Python {
    foreach ($cmd in @('py', 'python3', 'python')) {
        $exe = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($exe) {
            & $cmd -c "import sys; sys.exit(0 if sys.version_info>=(3,8) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) { return $cmd }
        }
    }
    return $null
}

try {
    # ── Python ───────────────────────────────────────────────────────────────
    $py = Find-Python
    if (-not $py) {
        Write-Error "Python 3.8+ is required. Install it from https://python.org"
        exit 1
    }

    # ── Git ──────────────────────────────────────────────────────────────────
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "git is required. Install it from https://git-scm.com"
        exit 1
    }

    # ── Parse --full flag (consumed here, not forwarded to scaffold) ──────────
    $isFull = $false
    $passThrough = @()
    foreach ($arg in $args) {
        if ($arg -eq '--full') { $isFull = $true }
        else { $passThrough += $arg }
    }

    # ── Clone + scaffold ──────────────────────────────────────────────────────
    Write-Host "harness-kit: installing into $(Get-Location) ..."
    git clone --depth 1 --quiet $repo $tmp

    $script = Join-Path $tmp "skills\scripts\scaffold_harness.py"
    $scriptArgs = @('--target', (Get-Location).Path)
    if (-not $isFull) { $scriptArgs += '--governance-only' }
    $scriptArgs += $passThrough

    & $py $script @scriptArgs

    Write-Host ""
    if ($isFull) {
        Write-Host "Done (full harness). Edit AGENTS.md, fill feature_list.json, then:"
        Write-Host "  py harness\harness.py --mock --goal 'your goal here'"
    } else {
        Write-Host "Done. Edit AGENTS.md (or CLAUDE.md) to customize rules for your project."
        Write-Host "Supported tools: Claude Code, Cursor, Codex, Windsurf, and any AI that reads your instruction file."
    }

} finally {
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
}
