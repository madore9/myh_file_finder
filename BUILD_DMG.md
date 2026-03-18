# Building the DMG (my.File Tool)

The app (Sensitive / Duplicates / Large / String search) is built from this folder.

## Prerequisites

- macOS
- Python 3 with `pip` (e.g. Python 3.10+ from python.org or Homebrew)
- Dependencies: `pip3 install PyQt5 py2app`

## Generate the DMG

From the **LargeFileFinder** directory:

```bash
cd /path/to/macApps/LargeFileFinder
chmod +x build_dmg.sh
./build_dmg.sh
```

This will:

1. Check/install PyQt5 and py2app
2. Build the `.app` with py2app (bundles `large_file_finder_v4.py` and `sensitive_scanner.py`)
3. Create a styled DMG

Output: **`MyFileTool.dmg`** in the same folder.

## Install

1. Double-click `MyFileTool.dmg`
2. Drag **my.File Tool** to Applications
3. Eject the disk image and open the app from Applications or Spotlight

## Windows .exe

To build a Windows executable, run **on Windows**:

```bash
build_exe.bat
```

This produces `dist\MyFileTool.exe` (one-file, no console).
