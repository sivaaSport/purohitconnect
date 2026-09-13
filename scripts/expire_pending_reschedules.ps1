# Hourly reschedule expiry + maintenance jobs (Windows Task Scheduler)
#
# Install:
#   powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_scheduled_jobs.ps1
#
# Manual run:
#   powershell -ExecutionPolicy Bypass -File .\scripts\expire_pending_reschedules.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$logDir = Join-Path $Root "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}
$logFile = Join-Path $logDir "scheduled_jobs.log"

function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $logFile -Value $line
    Write-Host $line
}

try {
    $venvPython = Join-Path $Root "venv\Scripts\python.exe"
    $python = if (Test-Path $venvPython) { $venvPython } else { "python" }

    if (-not $env:DJANGO_SETTINGS_MODULE) {
        # Prefer local/dev unless production is explicitly set in the environment.
        $env:DJANGO_SETTINGS_MODULE = "config.settings.development"
    }

    Write-Log "Starting run_scheduled_jobs with $env:DJANGO_SETTINGS_MODULE using $python"
    $output = & $python manage.py run_scheduled_jobs 2>&1
    $exitCode = $LASTEXITCODE
    foreach ($line in $output) {
        Write-Log "$line"
    }
    if ($exitCode -ne 0) {
        throw "run_scheduled_jobs exited with code $exitCode"
    }
    Write-Log "Completed successfully"
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}
