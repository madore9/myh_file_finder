@echo off
REM ============================================================
REM Build my.File Tool Windows .exe
REM Run this on Windows (double-click or: build_exe.bat)
REM Requires: Python 3.8+ with pip, PyQt5
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================
echo   Building my.File Tool (.exe)
echo ============================================
echo.

REM Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo   Python not found. Install from https://www.python.org/downloads/
        echo   Check "Add Python to PATH" during install.
        pause
        exit /b 1
    )
    set "PY=py -3"
) else (
    set "PY=python"
)

echo   Using: %PY%
echo.

REM Install PyInstaller and PyQt5 if needed
echo   Checking PyInstaller and PyQt5...
%PY% -m pip install --quiet pyinstaller PyQt5
if %errorlevel% neq 0 (
    echo   Failed to install dependencies.
    pause
    exit /b 1
)

REM Build one-file .exe (no console window for GUI app)
REM sensitive_scanner.py is imported by the main script; include it explicitly for reliability
echo.
echo   Building .exe (this may take a minute)...
%PY% -m PyInstaller --onefile --windowed --clean ^
    --name "MyFileTool" ^
    --add-data "sensitive_scanner.py;." ^
    large_file_finder_v4.py

if %errorlevel% neq 0 (
    echo.
    echo   Build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build complete
echo ============================================
echo.
echo   EXE: dist\MyFileTool.exe
echo.
echo   Run it on Windows. Use Mode: Sensitive / Duplicates / Large / String search
echo   from the top of the app.
echo.
pause
