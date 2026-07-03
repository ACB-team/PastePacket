@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set LOG=%cd%\build_spec.log
if exist "%LOG%" del "%LOG%"
where py >nul 2>nul && (set PY_CMD=py -3) || (set PY_CMD=python)
%PY_CMD% -m venv .venv >> "%LOG%" 2>&1
set VENV_PY=%cd%\.venv\Scripts\python.exe
"%VENV_PY%" -m pip install --upgrade pip >> "%LOG%" 2>&1
"%VENV_PY%" -m pip install -r requirements.txt >> "%LOG%" 2>&1
"%VENV_PY%" -m PyInstaller --noconfirm --clean PastePacket.spec >> "%LOG%" 2>&1
type "%LOG%"
pause
