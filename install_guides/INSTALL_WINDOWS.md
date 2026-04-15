# Zonetic Installation Guide (Windows)

Follow these steps to configure the Zonetic CLI on Windows. This process uses a PowerShell script to automate dependency checks, directory setup, and environment variables.

## 1. Prerequisites

You must have **Git** and **Python 3** installed. 
Verify them by running these commands in PowerShell:

```powershell
git --version
python --version
```

## 2. Quick Installation (Automated)

Open **PowerShell** and run the following command. This will download and execute the installer, setting up Zonetic in `~/.zonetic` and configuring the global `zon` command:

```powershell
irm https://raw.githubusercontent.com/alve-dev/zonetic-lang-tree-walker-version/refs/heads/main/install_windows.ps1 | iex
```

> [!IMPORTANT]
> **Restart your Terminal:** Windows needs a fresh session to recognize the new "Path" variables. Close and reopen PowerShell or CMD after installation.

## 3. Full Installation

To download the entire repository, including `examples/` and `docs/`:

```powershell
irm https://raw.githubusercontent.com/alve-dev/zonetic-lang-tree-walker-version/refs/heads/main/install_windows_complete.ps1 | iex
```

## 4. Keep Zonetic Updated

Updating is now a built-in feature. No more manual downloads:

```bash
zon update
```

## 5. Verify Installation

Check if Zonny is active:

```bash
zon vers
```

---

## Troubleshooting

### Script Execution Error
If Windows blocks the installer, run this command once to allow local scripts, then try the installation again:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 'zon' is not recognized
1. **Restart PowerShell:** This is mandatory.
2. **Manual Check:** Ensure `$HOME\.zonetic\scripts` is in your Environment Variables Path.

## Uninstallation

To remove Zonetic completely:

```powershell
# Delete the folder
Remove-Item -Recurse -Force "$HOME\.zonetic"
# Remember to manually remove the entry from your Environment Variables Path.
```

## Quick Start: REPL Mode

How to use `zon repl`:

1. **Enter the REPL**:
   ```powershell
   zon repl
   ```
2. **Execute**: Type `EOF` on a new line or press `Ctrl+Z and Enter`.

```powershell
>> print("Zonetic on Windows is alive!")
>> EOF
```

> [!TIP]
> This mode is perfect for testing logic or syntax quickly. Once the output is displayed, the temporary environment is wiped clean.
