Write-Host "[ ⌐■_■] < ( Starting FULL Zonetic setup for WINDOWS... )"

# (Check dependencies logic same as above...)
$InstallDir = "$HOME\.zonetic"

if (Test-Path $InstallDir) {
    $Choice = Read-Host "[ ⌐■_■] < ( $InstallDir exists. Overwrite? (y/n)"
    if ($Choice -ne "y") { exit 0 }
    Remove-Item -Recurse -Force $InstallDir
}

# Clone full repo
Write-Host "[ ⌐■_■] < ( Cloning full repository... )"
git clone https://github.com/alve-dev/zonetic-lang-tree-walker-version.git $InstallDir

# Set Path
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$NewPath = "$InstallDir\scripts"
if ($UserPath -notlike "*$NewPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$NewPath", "User")
}

Write-Host "[ ⌐■_■] < ( Full installation finished at $InstallDir )"

