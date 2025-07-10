@echo off
REM Closer Windows Launcher - Batch wrapper
REM This file launches the PowerShell script for easier double-click execution

echo Starting Closer AI Companion...
echo.

REM Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if errorlevel 1 (
    echo Error: PowerShell is not available on this system.
    echo Please ensure PowerShell is installed and try again.
    pause
    exit /b 1
)

REM Launch the PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*

REM If the script exits with an error, pause to show the error
if errorlevel 1 (
    echo.
    echo Closer encountered an error. Check the output above for details.
    pause
) 