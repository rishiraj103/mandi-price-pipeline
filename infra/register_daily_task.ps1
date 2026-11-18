# Register the daily ingest with Windows Task Scheduler: 07:00 every day, and as soon as
# possible after a missed start (laptop off at 7). Run once: powershell -File infra\register_daily_task.ps1
$cmd = Join-Path $PSScriptRoot "run_daily.cmd"
$action = New-ScheduledTaskAction -Execute $cmd
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "mandi-ingest-daily" -Action $action -Trigger $trigger -Settings $settings -Force |
    Select-Object TaskName, State
