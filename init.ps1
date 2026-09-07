$ErrorActionPreference = "Stop"

Write-Host "=== Harness Kit — Verification ==="

Write-Host "`n[1/2] Compiling all template Python files..."
Get-ChildItem skills/templates/*.py | ForEach-Object {
    py -m py_compile $_.FullName
    Write-Host "  OK  $($_.Name)"
}

Write-Host "`n[2/2] Running regression suite..."
py test_skill.py

Write-Host "`nVerification passed."
