# Registers an hourly Windows Task Scheduler job for PurohitConnect maintenance.
# Run from an elevated PowerShell if task creation is denied:
#   powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_scheduled_jobs.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $PSScriptRoot "expire_pending_reschedules.ps1"
$TaskName = "PurohitConnect\ExpirePendingReschedules"

if (-not (Test-Path $ScriptPath)) {
    throw "Missing script: $ScriptPath"
}

$action = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

# Start a few minutes from now so the first hourly boundary is soon.
$start = (Get-Date).AddMinutes(2).ToString("HH:mm")

Write-Host "Creating scheduled task: $TaskName"
Write-Host "Script: $ScriptPath"
Write-Host "Schedule: hourly, first run around $start"

schtasks /Create `
    /TN $TaskName `
    /TR $action `
    /SC HOURLY `
    /ST $start `
    /RL LIMITED `
    /F | Out-Host

Write-Host ""
Write-Host "Verify with:"
Write-Host "  schtasks /Query /TN `"$TaskName`" /V /FO LIST"
Write-Host "Run once now with:"
Write-Host "  schtasks /Run /TN `"$TaskName`""
Write-Host "Logs:"
Write-Host "  $Root\logs\scheduled_jobs.log"
Write-Host "Uninstall:"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\uninstall_windows_scheduled_jobs.ps1"
