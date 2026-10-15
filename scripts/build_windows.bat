@echo off
setlocal enabledelayedexpansion

echo ====================================================
echo         Briefly - Windows Build Script
echo ====================================================

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller pytest

echo [2/3] Running tests...
set QT_QPA_PLATFORM=offscreen
pytest tests
if %errorlevel% neq 0 (
    echo [ERROR] Tests failed! Aborting build.
    pause
    exit /b 1
)

echo [3/3] Packaging Briefly with PyInstaller...
pyinstaller --clean briefly.spec

echo.
echo ====================================================
echo  Build completed successfully!
echo  Output folder: dist\Briefly\
echo  Executable: dist\Briefly\Briefly.exe
echo ====================================================
