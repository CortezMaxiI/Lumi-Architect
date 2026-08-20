<#
.SYNOPSIS
Installs system dependencies and sets up the Python environment for Lumi: Architect.

.DESCRIPTION
This script follows the Brain-Forge split and idempotency principles:
1. Discovery Phase: Checks if Python 3 is installed.
2. Forging Phase: Installs Python 3 via winget if missing.
3. Setup Phase: Creates a virtual environment and installs Python dependencies.
#>

$ErrorActionPreference = "Stop"

Write-Host "[*] Starting Setup for Lumi: Architect..." -ForegroundColor Cyan

# --- Discovery Phase ---
$pythonInstalled = $false
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $pythonVersion -match "Python 3") {
        $pythonInstalled = $true
        Write-Host "[+] Python 3 is already installed: $pythonVersion" -ForegroundColor Green
    }
} catch {
    # Python not found
}

# --- Forging Phase ---
if (-not $pythonInstalled) {
    Write-Host "[-] Python 3 not found. Installing via winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.11 --exact --accept-package-agreements --accept-source-agreements
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# --- Setup Phase (Python Environment) ---
$venvPath = Join-Path $PSScriptRoot ".venv"
$requirementsPath = Join-Path $PSScriptRoot "Lumi-Architect\requirements.txt"

if (-not (Test-Path $venvPath)) {
    Write-Host "[*] Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv $venvPath
} else {
    Write-Host "[+] Virtual environment already exists." -ForegroundColor Green
}

Write-Host "[*] Installing Python dependencies..." -ForegroundColor Cyan
$pipExecutable = Join-Path $venvPath "Scripts\python.exe"

# We use python.exe -m pip to bypass execution policies for Activate.ps1
& $pipExecutable -m pip install --upgrade pip
& $pipExecutable -m pip install -r $requirementsPath

Write-Host "[+] Setup complete! You can now run the software." -ForegroundColor Green
