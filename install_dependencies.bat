@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install --upgrade PySide6
pause
