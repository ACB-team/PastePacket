@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
  echo Python not found. Please install Python 3.10+ first.
  pause
  exit /b 1
)

echo [2/4] Installing build dependencies...
python -m pip install --upgrade pyinstaller PySide6
if errorlevel 1 (
  echo Failed to install dependencies.
  pause
  exit /b 1
)

echo [3/4] Cleaning old build files...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q PastePacketQt.spec 2>nul

echo [4/4] Building windowed EXE without console...
python -m PyInstaller --onefile --windowed --name PastePacketQt pastepacket_qt_drag_v040.py

echo.
echo Build finished.
echo EXE path: %cd%\dist\PastePacketQt.exe
echo.
pause
