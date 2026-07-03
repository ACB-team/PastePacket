@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set LOG=%cd%\build.log
if exist "%LOG%" del "%LOG%"

echo [PastePacket] Build started. > "%LOG%"
echo Working dir: %cd% >> "%LOG%"
echo. >> "%LOG%"

rem Prefer the Windows Python launcher. Fall back to python.exe.
set PY_CMD=
where py >nul 2>nul
if not errorlevel 1 (
  set PY_CMD=py -3
) else (
  where python >nul 2>nul
  if not errorlevel 1 (
    set PY_CMD=python
  )
)

if "%PY_CMD%"=="" (
  echo [ERROR] Python not found. Install Python 3.10+ and tick "Add Python to PATH". >> "%LOG%"
  type "%LOG%"
  pause
  exit /b 1
)

echo [1/5] Python version >> "%LOG%"
%PY_CMD% --version >> "%LOG%" 2>&1
if errorlevel 1 goto fail

rem Create an isolated virtual environment to avoid dirty global packages.
echo. >> "%LOG%"
echo [2/5] Creating virtual environment .venv >> "%LOG%"
%PY_CMD% -m venv .venv >> "%LOG%" 2>&1
if errorlevel 1 goto fail

set VENV_PY=%cd%\.venv\Scripts\python.exe
if not exist "%VENV_PY%" (
  echo [ERROR] venv python not found: %VENV_PY% >> "%LOG%"
  goto fail
)

echo. >> "%LOG%"
echo [3/5] Installing dependencies >> "%LOG%"
"%VENV_PY%" -m pip install --upgrade pip >> "%LOG%" 2>&1
if errorlevel 1 goto fail
"%VENV_PY%" -m pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 goto fail

echo. >> "%LOG%"
echo [4/5] Building no-console exe >> "%LOG%"
"%VENV_PY%" -m PyInstaller --noconfirm --clean --onefile --windowed --name PastePacket PastePacket.py >> "%LOG%" 2>&1
if errorlevel 1 goto fail

echo. >> "%LOG%"
echo [5/5] Checking output >> "%LOG%"
if exist "%cd%\dist\PastePacket.exe" (
  echo [OK] Build finished: %cd%\dist\PastePacket.exe >> "%LOG%"
  type "%LOG%"
  echo.
  echo [OK] Build finished: %cd%\dist\PastePacket.exe
  pause
  exit /b 0
) else (
  echo [ERROR] dist\PastePacket.exe was not created. >> "%LOG%"
  goto fail
)

:fail
echo. >> "%LOG%"
echo [ERROR] Build failed. Full log saved to: %LOG% >> "%LOG%"
type "%LOG%"
echo.
echo [ERROR] Build failed. Please send build.log to diagnose.
pause
exit /b 1
