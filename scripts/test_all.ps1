#!/usr/bin/env pwsh
# Legacy2Lake CI Test Runner
# Runs: pytest (backend unit tests) + vitest (frontend component tests)
# Exit code 1 if any suite fails.

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "Legacy2Lake CI Test Runner" -ForegroundColor Cyan
Write-Host "Root: $Root"
Write-Host ""

# Activate venv if present, use venv python explicitly
$VenvActivate = Join-Path $Root ".venv\Scripts\Activate.ps1"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvActivate) {
    & $VenvActivate
}
# Prefer venv python when available, fall back to PATH python
$PyExe = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

# 1 - Backend: pytest
Write-Host "[1/2] Backend: pytest" -ForegroundColor Yellow
Push-Location $Root
& $PyExe -m pytest -q tests/unit/
$PytestExit = $LASTEXITCODE
Pop-Location

if ($PytestExit -eq 0) {
    Write-Host "PASS - All backend tests passed" -ForegroundColor Green
} else {
    Write-Host "FAIL - pytest reported failures (exit $PytestExit)" -ForegroundColor Red
}

Write-Host ""

# 2 - Frontend: vitest
Write-Host "[2/2] Frontend: vitest" -ForegroundColor Yellow
Push-Location $Root
npm run test --workspace=web
$VitestExit = $LASTEXITCODE
Pop-Location

if ($VitestExit -eq 0) {
    Write-Host "PASS - All frontend tests passed" -ForegroundColor Green
} else {
    Write-Host "FAIL - vitest reported failures (exit $VitestExit)" -ForegroundColor Red
}

Write-Host ""

# Summary
if ($PytestExit -ne 0 -or $VitestExit -ne 0) {
    Write-Host "RESULT: FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "RESULT: ALL TESTS PASSED" -ForegroundColor Green
    exit 0
}

