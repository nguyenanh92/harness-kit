# install.ps1 — Add an agent harness to your project.
# Run from your project root:
#   irm https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.ps1 | iex
#
# Optional flags passed through to the scaffold script:
#   --agent-file CLAUDE.md   (default: AGENTS.md)
#   --force                  (overwrite existing files)
$ErrorActionPreference = 'Stop'

$repo = "https://github.com/nguyenanh92/harness-kit.git"
$tmp  = Join-Path $env:TEMP "harness-kit-$(Get-Random)"

function Find-Python {
    foreach ($cmd in @('py', 'python3', 'python')) {
        $exe = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($exe) {
            $ok = & $cmd -c "import sys; sys.exit(0 if sys.version_info>=(3,8) else 1)" 2>$null
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

    # ── Clone + scaffold ─────────────────────────────────────────────────────
    Write-Host "harness-kit: installing into $(Get-Location) ..."
    git clone --depth 1 --quiet $repo $tmp

    $script = Join-Path $tmp "skills\scripts\scaffold_harness.py"
    & $py $script --target (Get-Location).Path --governance-only @args

    Write-Host ""
    Write-Host "Done. Edit AGENTS.md (or CLAUDE.md) to customize rules for your project."
    Write-Host "Supported tools: Claude Code, Cursor, Codex, Windsurf, and any AI that reads your instruction file."

} finally {
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
}
