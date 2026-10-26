@echo off
cd /d "%~dp0"

if not exist "dbt-env\Scripts\python.exe" (
    echo Project Python environment was not found.
    pause
    exit /b 1
)

"dbt-env\Scripts\python.exe" demo_controller.py

if errorlevel 1 (
    echo.
    echo The demo controller exited with an error.
    pause
)