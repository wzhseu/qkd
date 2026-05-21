@echo off
setlocal
cd /d "%~dp0"
".venv38_project\python.exe" run_gateway.py
endlocal
