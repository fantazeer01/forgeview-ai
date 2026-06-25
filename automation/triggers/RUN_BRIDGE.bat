@echo off
setlocal

echo ForgeView Local Shorts Generator Bridge
echo ======================================
echo.

set "BRIDGE_SCRIPT=D:\ForgeViewAI\content\publishing\local_bridge.py"
set "GENERATOR_DIR=D:\ForgeViewAI\content\video\shorts-generator"
set "PYTHON_CMD="

if exist "%GENERATOR_DIR%\.venv\Scripts\python.exe" (
  set "PYTHON_CMD=%GENERATOR_DIR%\.venv\Scripts\python.exe"
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
  echo Install Python and try again.
  echo.
  pause
  exit /b 1
)

if not exist "%BRIDGE_SCRIPT%" (
  echo ERROR: Bridge script not found:
  echo %BRIDGE_SCRIPT%
  echo.
  pause
  exit /b 1
)

echo Starting local bridge...
echo.
%PYTHON_CMD% "%BRIDGE_SCRIPT%"

echo.
pause
