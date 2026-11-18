# Register the daily ingest with Windows Task Scheduler: 07:00 every day, and as soon as
# possible after a missed start (laptop off at 7). pythonw runs it without a console window.
# Run once: powershell -ExecutionPolicy Bypass -File infra\register_daily_task.ps1
$root = Split-Path $PSScriptRoot -Parent
$action = New-ScheduledTaskAction -Execute (Join-Path $root ".venv\Scripts\pythonw.exe") `
    -Argument "-m ingest.daily" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "mandi-ingest-daily" -Action $action -Trigger $trigger -Settings $settings -Force |
    Select-Object TaskName, State
