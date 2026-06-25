@echo off
setlocal

cd /d "%~dp0"

echo ForgeView Shorts Generator
echo ==========================
echo.

set "PYTHON_CMD="

if exist ".venv\Scripts\python.exe" (
  set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
  where py >nul 2>nul
  if not errorlevel 1 (
  set "PYTHON_CMD=py -3"
  ) else (
    where python >nul 2>nul
    if not errorlevel 1 (
      set "PYTHON_CMD=python"
    )
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
if errorlevel 1 (
  echo ERROR: FFmpeg was not found in PATH.
  echo.
  echo Install FFmpeg with:
  echo winget install Gyan.FFmpeg
  echo.
  echo Then restart this window and double-click RUN_SHORTS.bat again.
  echo.
  pause
  exit /b 1
)

echo Checking Python requirements...
%PYTHON_CMD% -c "import PIL" >nul 2>nul
if errorlevel 1 (
  echo Installing Python requirements...
  %PYTHON_CMD% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo ERROR: Could not install requirements.
    pause
    exit /b 1
  )
)

echo.
echo Rendering example_short.json...
if not exist "D:\ForgeViewAI\output\media\videos" (
  mkdir "D:\ForgeViewAI\output\media\videos"
)

%PYTHON_CMD% render_short.py --input example_short.json --output "D:\ForgeViewAI\output\media\videos\short.mp4" --workdir "D:\ForgeViewAI\output\content\shorts-generator\work"
if errorlevel 1 (
  echo.
  echo ERROR: Render failed.
  pause
  exit /b 1
)

echo.
echo SUCCESS: Video created.
echo Output:
echo D:\ForgeViewAI\output\media\videos\short.mp4
echo.

echo Sending to Telegram...
%PYTHON_CMD% send_telegram_video.py
if errorlevel 1 (
  echo.
  echo ERROR: Telegram send failed.
  pause
  exit /b 1
)

pause
