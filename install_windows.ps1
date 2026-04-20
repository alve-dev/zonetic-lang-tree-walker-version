if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "[ ⌐■_■] <(`"Starting Zonetic setup for WINDOWS...`")" -ForegroundColor Cyan

function Refresh-Env {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Check-And-Install {
    param (
        [string]$CommandName,
        [string]$PackageId
    )

    $working = $false
    if (Get-Command $CommandName -ErrorAction SilentlyContinue) {
        if ($CommandName -eq "g++") {
            $working = g++ --version 2>$null
        } else {
            $working = $true
        }
    }

    if (!$working) {
        Write-Host "[ ! ] $CommandName is missing or not working." -ForegroundColor Yellow
        $answer = Read-Host "[ ⌐■_■] <(`"Install $CommandName now? (y/n)`") "
        
        if ($answer.ToLower() -eq "y") {
            Write-Host "[ ⌐■_■] <(`"Launching winget for $CommandName...`")" -ForegroundColor Green
            winget install --exact --id $PackageId --accept-source-agreements --accept-package-agreements
            
            Refresh-Env
            
            if ($PackageId -eq "MSYS2.MSYS2") {
                Write-Host "[ ⌐■_■] <(`"Installing GCC 15 via MSYS2. Please wait...`")" -ForegroundColor Cyan
                $bashPath = "C:\msys64\usr\bin\bash.exe"
                if (Test-Path $bashPath) {
                    & $bashPath -lc "pacman -S --noconfirm mingw-w64-ucrt-x86_64-gcc"
                }
                
                $mingwPath = "C:\msys64\ucrt64\bin"
                if (Test-Path $mingwPath) {
                    $oldPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
                    if ($oldPath -notlike "*$mingwPath*") {
                        [System.Environment]::SetEnvironmentVariable("Path", "$oldPath;$mingwPath", "User")
                        $env:Path += ";$mingwPath"
                        Write-Host "[ ⌐■_■] <(`"g++ linked successfully: $mingwPath`")" -ForegroundColor Green
                    }
                }
            }
        } else {
            Write-Host "[ X_X] <(`"Error: $CommandName is required. Aborting.`")" -ForegroundColor Red
            Pause
            exit 1
        }
    } else {
        Write-Host "[ ✓ ] $CommandName is already installed." -ForegroundColor Green
    }
}

Check-And-Install "git" "Git.Git"
Check-And-Install "python" "Python.Python.3.12"
Check-And-Install "g++" "MSYS2.MSYS2"

$InstallDir = Join-Path $HOME ".zonetic"
$ZoncDir    = Join-Path $InstallDir ".zonc"
$ZonvmDir   = Join-Path $InstallDir ".zonvm"

if (Test-Path $InstallDir) {
    $choice = Read-Host "[ ? ] $InstallDir already exists. Overwrite? (y/n)"
    if ($choice.ToLower() -eq "y") {
        Remove-Item -Recurse -Force $InstallDir | Out-Null
    }
}

New-Item -ItemType Directory -Path $ZoncDir -Force | Out-Null
New-Item -ItemType Directory -Path $ZonvmDir -Force | Out-Null

Write-Host "[ ⌐■_■] <(`"Cloning repositories...`")" -ForegroundColor Cyan
Set-Location $ZoncDir
git init -q
try { git remote add origin https://github.com 2>$null } catch {}
git pull origin main -q

Set-Location $ZonvmDir
git init -q
try { git remote add origin https://github.com 2>$null } catch {}
git pull origin main -q

$LauncherPath = Join-Path $ZoncDir "scripts"
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$LauncherPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$LauncherPath", "User")
}

Write-Host "`n------------------------------------------------" -ForegroundColor Cyan
Write-Host "[ ⌐■_■] <(`"Zonetic installed successfully!`")" -ForegroundColor Green
Write-Host "[ ! ] IMPORTANT: RESTART your terminal/VS Code now." -ForegroundColor Yellow
Write-Host "------------------------------------------------"
Pause
