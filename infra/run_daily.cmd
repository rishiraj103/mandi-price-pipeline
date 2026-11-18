@echo off
rem Daily ingest, started by Windows Task Scheduler (see register_daily_task.ps1).
cd /d "%~dp0.."
if not exist data\logs mkdir data\logs
.venv\Scripts\python.exe -m ingest.daily >> data\logs\ingest_daily.log 2>&1
