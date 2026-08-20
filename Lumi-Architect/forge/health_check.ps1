<#
.SYNOPSIS
    Lumi: Architect - Health Check
    Post-Forge verification to ensure all installed tools are operational.

.DESCRIPTION
    This script reads the Architecture Manifest and verifies that each package
    is correctly installed and accessible from the command line.

.PARAMETER ManifestPath
    Path to the Architecture Manifest JSON file used during the Forge.

.PARAMETER Detailed
    Show detailed output for each check.

.EXAMPLE
    .\health_check.ps1 -ManifestPath ".\output\manifest.json"

.EXAMPLE
    .\health_check.ps1 -ManifestPath ".\output\manifest.json" -Detailed

.NOTES
    Author: Lumi: Architect
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateScript({ Test-Path $_ -PathType Leaf })]
    [string]$ManifestPath,

    [Parameter(Mandatory = $false)]
    [switch]$Detailed
)

# =============================================================================
# CONFIGURATION
# =============================================================================

$Script:Config = @{
    Version = "1.0.0"
}

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

function Write-HealthLog {
    param(
        [string]$Message,
        [ValidateSet("Info", "Success", "Warning", "Error", "Header")]
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    switch ($Level) {
        "Header" {
            Write-Host ""
            Write-Host ("=" * 60) -ForegroundColor Cyan
            Write-Host "  $Message" -ForegroundColor Cyan
            Write-Host ("=" * 60) -ForegroundColor Cyan
        }
        "Success" {
            Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
            Write-Host "[PASS] " -NoNewline -ForegroundColor Green
            Write-Host $Message -ForegroundColor Green
        }
        "Warning" {
            Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
            Write-Host "[WARN] " -NoNewline -ForegroundColor Yellow
            Write-Host $Message -ForegroundColor Yellow
        }
        "Error" {
            Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
            Write-Host "[FAIL] " -NoNewline -ForegroundColor Red
            Write-Host $Message -ForegroundColor Red
        }
        "Info" {
            Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
            Write-Host "[INFO] " -NoNewline -ForegroundColor Blue
            Write-Host $Message -ForegroundColor White
        }
    }
}

# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================

function Test-ToolHealth {
    <#
    .SYNOPSIS
        Tests if a specific tool is accessible and returns version info.
    #>
    param(
        [string]$DisplayName,
        [string]$VersionCommand,
        [switch]$Detailed
    )
    
    $result = @{
        Name    = $DisplayName
        Healthy = $false
        Version = $null
        Output  = $null
        Error   = $null
    }
    
    if ([string]::IsNullOrWhiteSpace($VersionCommand)) {
        $result.Error = "No version command specified"
        return $result
    }
    
    try {
        # Execute version check
        $output = Invoke-Expression $VersionCommand 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0 -or $null -eq $exitCode) {
            $result.Healthy = $true
            $result.Output = ($output | Out-String).Trim()
            
            # Extract version number
            if ($result.Output -match "\d+\.\d+(\.\d+)?(\.\d+)?") {
                $result.Version = $Matches[0]
            }
        }
        else {
            $result.Error = "Command returned exit code: $exitCode"
            $result.Output = ($output | Out-String).Trim()
        }
    }
    catch {
        $result.Error = $_.Exception.Message
    }
    
    return $result
}

function Test-PathAccessibility {
    <#
    .SYNOPSIS
        Verifies that an executable is accessible in the system PATH.
    #>
    param([string]$Executable)
    
    $cmd = Get-Command $Executable -ErrorAction SilentlyContinue
    return $null -ne $cmd
}

# =============================================================================
# REPORT GENERATION
# =============================================================================

function Show-HealthReport {
    param(
        [array]$Results,
        [string]$EnvironmentName
    )
    
    $healthy = ($Results | Where-Object { $_.Healthy }).Count
    $unhealthy = ($Results | Where-Object { -not $_.Healthy }).Count
    $total = $Results.Count
    $healthPercent = if ($total -gt 0) { [math]::Round(($healthy / $total) * 100) } else { 0 }
    
    Write-Host ""
    Write-Host ""
    
    # Determine overall status
    if ($unhealthy -eq 0) {
        # All healthy - show success banner
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Green
        Write-Host "  |                                                  |" -ForegroundColor Green
        Write-Host "  |     SYSTEM HEALTH CHECK: ALL SYSTEMS GO!         |" -ForegroundColor Green
        Write-Host "  |                                                  |" -ForegroundColor Green
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Green
        Write-Host ""
        Write-Host "     Environment: $EnvironmentName" -ForegroundColor Cyan
        Write-Host "     Health Score: $healthPercent% ($healthy/$total tools operational)" -ForegroundColor Green
        Write-Host ""
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Green
        Write-Host "  |  All installed tools are accessible and ready!   |" -ForegroundColor Green
        Write-Host "  |  Your development environment is fully forged.   |" -ForegroundColor Green
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Green
    }
    elseif ($healthy -gt $unhealthy) {
        # Mostly healthy
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Yellow
        Write-Host "  |                                                  |" -ForegroundColor Yellow
        Write-Host "  |     SYSTEM HEALTH CHECK: PARTIAL SUCCESS         |" -ForegroundColor Yellow
        Write-Host "  |                                                  |" -ForegroundColor Yellow
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "     Environment: $EnvironmentName" -ForegroundColor Cyan
        Write-Host "     Health Score: $healthPercent% ($healthy/$total tools operational)" -ForegroundColor Yellow
        Write-Host "     Issues Found: $unhealthy tool(s) need attention" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Yellow
        Write-Host "  |  Some tools may need PATH refresh or reinstall.  |" -ForegroundColor Yellow
        Write-Host "  |  Try restarting your terminal and re-running.    |" -ForegroundColor Yellow
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Yellow
    }
    else {
        # Mostly unhealthy
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Red
        Write-Host "  |                                                  |" -ForegroundColor Red
        Write-Host "  |     SYSTEM HEALTH CHECK: CRITICAL ISSUES         |" -ForegroundColor Red
        Write-Host "  |                                                  |" -ForegroundColor Red
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Red
        Write-Host ""
        Write-Host "     Environment: $EnvironmentName" -ForegroundColor Cyan
        Write-Host "     Health Score: $healthPercent% ($healthy/$total tools operational)" -ForegroundColor Red
        Write-Host "     Failed: $unhealthy tool(s) are not accessible" -ForegroundColor Red
        Write-Host ""
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Red
        Write-Host "  |  Multiple tools failed verification.             |" -ForegroundColor Red
        Write-Host "  |  Check the Forge logs and try reinstalling.      |" -ForegroundColor Red
        Write-Host "  +--------------------------------------------------+" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Detailed results table
    Write-Host "  DETAILED RESULTS:" -ForegroundColor Cyan
    Write-Host "  -----------------" -ForegroundColor Cyan
    
    foreach ($r in $Results) {
        $statusIcon = if ($r.Healthy) { "[OK]" } else { "[X] " }
        $statusColor = if ($r.Healthy) { "Green" } else { "Red" }
        $versionInfo = if ($r.Version) { "v$($r.Version)" } else { "N/A" }
        
        Write-Host "  $statusIcon " -NoNewline -ForegroundColor $statusColor
        Write-Host ("{0,-25}" -f $r.Name) -NoNewline -ForegroundColor White
        Write-Host " $versionInfo" -ForegroundColor $(if ($r.Healthy) { "Cyan" } else { "DarkGray" })
        
        if (-not $r.Healthy -and $r.Error) {
            Write-Host "       Error: $($r.Error)" -ForegroundColor DarkRed
        }
    }
    
    Write-Host ""
    
    return @{
        TotalChecks   = $total
        Healthy       = $healthy
        Unhealthy     = $unhealthy
        HealthPercent = $healthPercent
        AllHealthy    = ($unhealthy -eq 0)
    }
}

# =============================================================================
# MAIN HEALTH CHECK
# =============================================================================

function Start-HealthCheck {
    param(
        [string]$ManifestPath,
        [switch]$Detailed
    )
    
    # Banner
    Write-Host ""
    Write-Host "  LUMI: ARCHITECT - HEALTH CHECK" -ForegroundColor Magenta
    Write-Host "  Post-Forge System Verification" -ForegroundColor DarkMagenta
    Write-Host "  Version $($Script:Config.Version)" -ForegroundColor DarkGray
    Write-Host ""
    
    # Load manifest
    Write-HealthLog "LOADING MANIFEST" -Level Header
    Write-HealthLog "Reading: $ManifestPath" -Level Info
    
    try {
        $manifestContent = Get-Content -Path $ManifestPath -Raw -Encoding UTF8
        $manifest = $manifestContent | ConvertFrom-Json
        
        $envName = $manifest.target_environment.name
        $envDesc = $manifest.target_environment.description
        
        Write-HealthLog "Environment: $envName" -Level Success
        Write-HealthLog "Description: $envDesc" -Level Info
    }
    catch {
        Write-HealthLog "Failed to parse manifest: $_" -Level Error
        return @{ Success = $false }
    }
    
    # Run health checks
    Write-HealthLog "VERIFYING INSTALLED TOOLS" -Level Header
    
    $results = @()
    $packages = $manifest.packages | Sort-Object -Property priority_level
    
    foreach ($pkg in $packages) {
        $displayName = $pkg.display_name
        $versionCmd = $pkg.version_check_command
        
        Write-HealthLog "Checking: $displayName..." -Level Info
        
        $checkResult = Test-ToolHealth -DisplayName $displayName -VersionCommand $versionCmd -Detailed:$Detailed
        $results += $checkResult
        
        if ($checkResult.Healthy) {
            $versionStr = if ($checkResult.Version) { " (v$($checkResult.Version))" } else { "" }
            Write-HealthLog "$displayName$versionStr - Operational" -Level Success
            
            if ($Detailed -and $checkResult.Output) {
                Write-Host "       Output: $($checkResult.Output.Substring(0, [Math]::Min(50, $checkResult.Output.Length)))..." -ForegroundColor DarkGray
            }
        }
        else {
            Write-HealthLog "$displayName - NOT ACCESSIBLE" -Level Error
            if ($checkResult.Error) {
                Write-Host "       Reason: $($checkResult.Error)" -ForegroundColor DarkRed
            }
        }
    }
    
    # Check post-install commands (npm, pip, etc.)
    $postCommands = $manifest.post_install_commands
    if ($postCommands -and $postCommands.Count -gt 0) {
        Write-HealthLog "VERIFYING POST-INSTALL TOOLS" -Level Header
        
        foreach ($cmd in $postCommands) {
            $command = $cmd.command
            $description = $cmd.description
            
            # Extract the tool name from the command
            $toolName = $description
            
            # Try to extract executable from common patterns
            if ($command -match "^(npm|pip|dotnet|cargo)\s+") {
                $parentTool = $Matches[1]
                
                # Check if parent tool is accessible
                if (Test-PathAccessibility -Executable $parentTool) {
                    Write-HealthLog "$toolName - Parent tool ($parentTool) accessible" -Level Success
                    $results += @{
                        Name    = $toolName
                        Healthy = $true
                        Version = "via $parentTool"
                    }
                }
                else {
                    Write-HealthLog "$toolName - Parent tool ($parentTool) not in PATH" -Level Warning
                    $results += @{
                        Name    = $toolName
                        Healthy = $false
                        Error   = "$parentTool not in PATH"
                    }
                }
            }
        }
    }
    
    # Generate and display report
    Write-HealthLog "GENERATING HEALTH REPORT" -Level Header
    $report = Show-HealthReport -Results $results -EnvironmentName $envName
    
    # Recommendations if issues found
    if (-not $report.AllHealthy) {
        Write-Host ""
        Write-Host "  RECOMMENDATIONS:" -ForegroundColor Yellow
        Write-Host "  -----------------" -ForegroundColor Yellow
        Write-Host "  1. Close and reopen your terminal to refresh PATH" -ForegroundColor White
        Write-Host "  2. Run 'refreshenv' if using Chocolatey" -ForegroundColor White
        Write-Host "  3. Log out and log back in for system-wide changes" -ForegroundColor White
        Write-Host "  4. Re-run the Forge for failed packages" -ForegroundColor White
        Write-Host ""
    }
    
    # Final status
    Write-Host ""
    if ($report.AllHealthy) {
        Write-Host "  Your development environment is ready to use!" -ForegroundColor Green
    }
    else {
        Write-Host "  Some tools need attention. See recommendations above." -ForegroundColor Yellow
    }
    Write-Host ""
    
    return @{
        Success = $report.AllHealthy
        Report  = $report
        Results = $results
    }
}

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

$result = Start-HealthCheck -ManifestPath $ManifestPath -Detailed:$Detailed

if ($result.Success) {
    exit 0
}
else {
    exit 1
}
