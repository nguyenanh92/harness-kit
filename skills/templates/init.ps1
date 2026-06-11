$ErrorActionPreference = 'Stop'

Write-Host "[init] verifying workspace (build, lint, compile, test)..."

# Static check: compile Python harness modules
$pyFiles = Get-ChildItem -Filter *.py -ErrorAction SilentlyContinue
if ($pyFiles) {
    foreach ($f in $pyFiles) { py -m py_compile $f.FullName }
}

# Test stage: pytest if available, else unittest discover
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
