# Removes the PurohitConnect hourly maintenance Task Scheduler job.

$ErrorActionPreference = "Stop"
$TaskName = "PurohitConnect\ExpirePendingReschedules"

Write-Host "Deleting scheduled task: $TaskName"
schtasks /Delete /TN $TaskName /F | Out-Host
Write-Host "Done."
