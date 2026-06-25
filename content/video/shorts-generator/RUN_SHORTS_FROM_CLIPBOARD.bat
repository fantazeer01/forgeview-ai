@echo off
setlocal

cd /d "%~dp0"

echo ForgeView Shorts Generator - Clipboard Mode
echo ===========================================
echo.
echo Reading JSON from clipboard...

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Clipboard | Set-Content -LiteralPath 'clipboard_short.json' -Encoding UTF8"
if not %errorlevel%==0 (
  echo.
  echo ERROR: Could not read clipboard.
  pause
  exit /b 1
)

set "PYTHON_CMD="

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_CMD=python"
  )
)

if "%PYTHON_CMD%"=="" (
  echo ERROR: Python was not found.
  echo.
  echo Install Python from:
  echo https://www.python.org/downloads/windows/
  echo.
  echo During install, enable: Add python.exe to PATH
  echo.
  pause
  exit /b 1
)

where ffmpeg >nul 2>nul
if not %errorlevel%==0 (
  echo ERROR: FFmpeg was not found in PATH.
  echo.
  echo Install FFmpeg with:
  echo winget install Gyan.FFmpeg
  echo.
  echo Then restart this window and double-click RUN_SHORTS_FROM_CLIPBOARD.bat again.
  echo.
  pause
  exit /b 1
)

echo Checking Python requirements...
%PYTHON_CMD% -c "import PIL" >nul 2>nul
if not %errorlevel%==0 (
  echo Installing Python requirements...
  %PYTHON_CMD% -m pip install -r requirements.txt
  if not %errorlevel%==0 (
    echo.
    echo ERROR: Could not install requirements.
    pause
    exit /b 1
  )
)

echo.
echo Validating clipboard_short.json...
%PYTHON_CMD% -m json.tool clipboard_short.json >nul
if not %errorlevel%==0 (
  echo.
  echo ERROR: Clipboard does not contain valid JSON.
  echo Copy the full Shorts draft JSON and try again.
  pause
  exit /b 1
)

echo.
echo Rendering clipboard_short.json...
%PYTHON_CMD% render_short.py --input clipboard_short.json --output output\short.mp4
if not %errorlevel%==0 (
  echo.
  echo ERROR: Render failed.
  pause
  exit /b 1
)

echo.
echo SUCCESS: Video created from clipboard JSON.
echo Output:
echo %~dp0output\short.mp4
echo.
pause
