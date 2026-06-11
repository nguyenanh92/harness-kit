$ErrorActionPreference = 'Stop'

Write-Host "[init] verifying workspace (build, lint, compile, test)..."

$HarnessDir = "{{HARNESS_DIR}}"

# Static check: compile harness modules if present.
if (Test-Path $HarnessDir) {
    py -m compileall -q $HarnessDir
}

# Test stage: pytest if available, else unittest discover.
if (Test-Path tests) {
    $pytest = Get-Command pytest -ErrorAction SilentlyContinue
    if ($pytest) {
        pytest -q
    } else {
        py -m unittest discover -s tests -v
    }
} else {
    Write-Host "[init] no tests/ directory yet - skipping test stage"
}

Write-Host "[init] OK - workspace is clean and restartable"
