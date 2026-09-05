@echo off
set "SCRIPT_DIR=%~dp0"
set "APP=%SCRIPT_DIR%server_check_status_gui.pyw"

where pyw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pyw "%APP%"
    exit /b 0
)

where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw "%APP%"
    exit /b 0
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    start "" python "%APP%"
    exit /b 0
)

echo Python was not found. Install Python 3, then open this file again.
pause
