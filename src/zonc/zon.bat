@echo off
set "PYTHON_CMD=python"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=py"
    ) else (
        echo [zon error]: Python not found.
        echo -- Please install it from python.org or the Microsoft Store.
        pause
        exit /b
    )
)

%PYTHON_CMD% "%~dp0main.py" %*
