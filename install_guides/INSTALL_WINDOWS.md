# Zonetic Installation Guide (Windows)

The repository includes a `zon.bat` launcher inside the `src/zonc/` directory. Follow these steps to configure the CLI globally.

## 1. Prerequisites

Ensure **Python 3.10+** is installed. Verify in PowerShell:

```powershell
python --version
```

## 2. Clone the Repository

Before cloning, ensure you are in a safe directory (like your User folder). **Do not install Zonetic inside C:\Windows or System32.**

Run these commands to go to your personal home folder and clone the project:

```powershell
cd $HOME
git clone https://github.com/alve-dev/zonetic-lang-tree-walker-version.git zonetic
```

**WARNING:** Avoid modifying or moving files inside the `zonetic/` directory after installation, as it will break the global `zon` command.

## 3. Get the Installation Path

Navigate to the compiler directory and get the full path to copy it:

```powershell
cd zonetic/src/zonc
(Get-Item .).FullName
```

*Copy the output of the last command (e.g., C:\Users\Name\zonetic\src\zonc).*

## 4. Add to Environment Variables

1. Open the **Start Menu**, search for "Environment Variables" and select **Edit the system environment variables**.
2. Click **Environment Variables**.
3. Under **User variables**, select **Path** and click **Edit**.
4. Click **New** and paste the path you copied in Step 3.
5. Click **OK** on all windows and **restart your terminal**.

**To reset your terminal, you can do the following:**
```powershell
exit
```
*(And then open a new terminal window).*

## 5. Verify Installation

Open a new PowerShell or CMD window and run:

```powershell
zon vers
```

---

## Troubleshooting

### Command not found
If `zon` is not recognized, ensure you restarted PowerShell after editing the Environment Variables.

### Broken Link
If you move the `zonetic` folder, you must update the Path in Environment Variables with the new location of `src/zonc`.

## Uninstallation

To remove the `zon` command, delete the entry from your Environment Variables Path.

## Quick Start: REPL Mode

Zonetic features a built-in **REPL** (Interactive Mode) that allows you to write and execute code on the fly without creating permanent files. It uses a temporary buffer that clears itself after execution.

### How to use `zon repl`

1. **Enter the REPL**:
   ```bash
   zon repl
   ```
2. **Write your code**: You can write multiple lines.
3. **Execute**: Type `EOF` on a new line or press `Ctrl+D` to trigger execution.

**Example:**
```bash
>> mut counter = 0 
>> while counter <= 5 {
>>    print(counter)
>>    counter += 1
>> }
>> EOF
```

**Result:**
```text
--- Executing ---
0
1
2
3
4
5
```

> [!TIP]
> This mode is perfect for testing logic or syntax quickly. Once the output is displayed, the temporary environment is wiped clean.
