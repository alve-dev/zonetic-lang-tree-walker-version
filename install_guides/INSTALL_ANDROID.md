# Zonetic Installation Guide (Android - Termux)

Follow these steps to configure the **Zonetic** command-line interface on Android. This process uses **Termux** to create a global environment for the compiler.

## 0. Install Termux (Read Carefully)

Termux is a terminal emulator that provides a Linux environment. **Do not use the Google Play Store version**, as it is outdated.

1.  **Download**: Go to the [Official F-Droid Page](https://f-droid.org).
2.  **Select Version**: Scroll down to the "Versions" or "Packages" section. Download the latest version available that **DOES NOT** have the "(beta)" tag in its name.
3.  **Install the APK**:
    *   Once downloaded, tap the file to install.
    *   **Security Prompt**: Android might say it is an "Unsafe App" because it's an APK.
    *   **How to bypass**: Tap on **"More details"** and then select **"Install anyway"**.
4.  **Open**: Launch Termux and wait for the "Installing bootstrap" process to finish.

## 1. Prerequisites

Zonetic requires Python 3.10 or higher. Update your packages and install the necessary tools:

```bash
pkg update && pkg upgrade
pkg install git python binutils
```

Verify your environment:

```bash
python --version
```

## 2. Clone the Repository

Clone the source code into a specific directory named 'zonetic':

```bash
git clone https://github.com zonetic
```

> [!CAUTION]
> **WARNING**: Do not modify, move, or delete files inside the `zonetic/` directory after installation. Doing so will break the compiler and the global command.

## 3. Navigate and Set Permissions

Move to the compiler source directory and grant execution permissions to the entry point:

```bash
cd zonetic/src/zonc
chmod +x main.py
```

## 4. Create the System Link

Link the script to the internal binary folder (no sudo required in Termux):

```bash
ln -s $(pwd)/main.py $PREFIX/bin/zon
```

## 5. Verify Installation

Test the installation by checking the version:

```bash
zon vers
```

---

## Troubleshooting

**Command not found**
If the terminal does not recognize the command immediately, restart Termux or run:
```bash
hash -r
```

**Broken Link**
The symbolic link depends on the absolute path of the source file. If you move the zonetic folder, you must recreate the link:
```bash
rm $PREFIX/bin/zon
cd new/path/to/zonetic/src/zonc
ln -s $(pwd)/main.py $PREFIX/bin/zon
```

## Uninstallation

To remove the `zon` command from your system:

```bash
rm $PREFIX/bin/zon
```
