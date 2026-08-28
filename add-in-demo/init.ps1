$ErrorActionPreference = 'Stop'

Write-Host "[init] verifying workspace (lint + build)..."

$AppDir = Join-Path $PSScriptRoot "outlook-copilot"

if (-not (Test-Path $AppDir)) {
    Write-Error "[init] outlook-copilot/ not found. Run F-001 scaffold first."
    exit 1
}

Push-Location $AppDir

if (-not (Test-Path "node_modules")) {
    Write-Host "[init] installing dependencies..."
    npm install
}

Write-Host "[init] lint..."
npm run lint

Write-Host "[init] build..."
npm run build

Write-Host "[init] OK - workspace is clean and restartable"
Pop-Location
