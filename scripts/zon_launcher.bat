@echo off
setlocal enabledelayedexpansion

:: [ ⌐■_■] <( Locating Zonetic home... )
:: %~dp0 is the folder of this script (scripts\)
set "SCRIPTS_DIR=%~dp0"
cd /d "%SCRIPTS_DIR%\.."
set "REPO_DIR=%cd%"
set "MAIN_PY=%REPO_DIR%\src\zonc\main.py"

:: Command: zon update
if "%1"=="update" (
    echo [ ⌐■_■] ^< ( Checking for updates on GitHub... )
    git -C "%REPO_DIR%" fetch origin main -q

    for /f "tokens=*" %%a in ('git -C "%REPO_DIR%" log -1 origin/main --pretty^=format:%%s') do set "REMOTE_MSG=%%a"
    for /f "tokens=*" %%a in ('git -C "%REPO_DIR%" log -1 --pretty^=format:%%s') do set "LOCAL_MSG=%%a"

    echo !REMOTE_MSG! | findstr /C:"[NOSTABLE]" >nul
    if !errorlevel! equ 0 (
        echo [ ⌐■_■] ^< ( Error: Remote version is [NOSTABLE]. Aborting... )
        exit /b 1
    )

    if "!REMOTE_MSG!"=="!LOCAL_MSG!" (
        echo [ ⌐■_■] ^< ( Already up to date: !LOCAL_MSG! )
        exit /b 0
    )

    echo [ ⌐■_■] ^< ( Updating to: !REMOTE_MSG! )
    git -C "%REPO_DIR%" reset --hard origin/main -q
    git -C "%REPO_DIR%" clean -fd -q
    echo [ ⌐■_■] ^< ( Update complete! )
    exit /b 0
)

:: Run compiler
if exist "%MAIN_PY%" (
    python "%MAIN_PY%" %*
) else (
    echo [ ⌐■_■] ^< ( Error: main.py not found at %MAIN_PY% )
    exit /b 1
)
