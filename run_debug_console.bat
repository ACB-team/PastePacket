@echo off
chcp 65001 >nul
cd /d "%~dp0"
python pastepacket_qt_drag_v040.py
pause
