# --- FORZAR ELEVACIÓN Y MANTENER VENTANA VISIBLE ---
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    # -NoExit evita que la ventana se cierre si hay un error al inicio
    # -Wait no se usa aquí para que el proceso actual pueda cerrarse (exit)
    Start-Process powershell.exe "-NoProfile -NoExit -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
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
            # --interactive asegura que si el instalador tiene GUI, se vea
            winget install --exact --id $PackageId --accept-source-agreements --accept-package-agreements --interactive
            
            Refresh-Env
            
            if ($PackageId -eq "MSYS2.MSYS2") {
                Write-Host "[ ⌐■_■] <(`"Installing GCC via MSYS2. Please wait...`")" -ForegroundColor Cyan
                $bashPath = "C:\msys64\usr\bin\bash.exe"
                
                # Esperar a que el ejecutable aparezca en disco
                while (!(Test-Path $bashPath)) { Start-Sleep -Seconds 2 }

                # Ejecutamos pacman en una ventana visible para dar confianza
                # -lc lanza el comando en el entorno login de MSYS2
                & $bashPath -lc "pacman -S --noconfirm mingw-w64-ucrt-x86_64-gcc"
                
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

# --- INSTALACIÓN DE DEPENDENCIAS ---
Check-And-Install "git" "Git.Git"
Check-And-Install "python" "Python.Python.3.12"
Check-And-Install "g++" "MSYS2.MSYS2"

# --- CONFIGURACIÓN DE DIRECTORIOS ---
# Usamos el perfil del usuario original incluso siendo admin
$TargetUser = [System.Environment]::GetEnvironmentVariable("UserName")
$InstallDir = "C:\Users\$TargetUser\.zonetic"
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

# --- DESCARGA DE COMPONENTES ---
Write-Host "[ ⌐■_■] <(`"Cloning repositories...`")" -ForegroundColor Cyan
Set-Location $ZoncDir
git init -q
try { git remote add origin https://github.com 2>$null } catch {}
git pull origin main

Set-Location $ZonvmDir
git init -q
try { git remote add origin https://github.com 2>$null } catch {}
git pull origin main

# --- PATH FINAL ---
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
