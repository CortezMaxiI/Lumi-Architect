<#
.SYNOPSIS
Runs the Lumi: Architect application.

.DESCRIPTION
This script starts the Python environment and executes the main program.
#>

$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$mainScript = Join-Path $PSScriptRoot "Lumi-Architect\main.py"

if (-not (Test-Path $venvPython)) {
    Write-Host "[-] Virtual environment not found. Please run setup_dependencies.ps1 first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $mainScript)) {
    Write-Host "[-] main.py not found in Lumi-Architect directory." -ForegroundColor Red
    exit 1
}

Write-Host "[*] Starting Lumi: Architect..." -ForegroundColor Cyan

# Set UTF-8 encoding to prevent Unicode errors with rich
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# Execute the application
& $venvPython $mainScript
