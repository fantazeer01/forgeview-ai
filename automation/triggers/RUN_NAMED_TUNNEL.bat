@echo off
setlocal

echo ForgeView Cloudflare Named Tunnel
echo =================================
echo.

where cloudflared >nul 2>nul
if errorlevel 1 (
  echo ERROR: cloudflared was not found.
  echo.
  echo Install Cloudflare Tunnel with:
  echo winget install Cloudflare.cloudflared
  echo.
  echo Then follow:
  echo D:\ForgeViewAI\content\docs\operations\CLOUDFLARE_NAMED_TUNNEL_SETUP.md
  echo.
  pause
  exit /b 1
)

echo This launcher expects a named tunnel called:
echo forgeview-local-bridge
echo.
echo It also expects cloudflared config.yml to route your hostname to:
echo http://127.0.0.1:8787
echo.
echo Start RUN_BRIDGE.bat before this file.
echo.

cloudflared tunnel run forgeview-local-bridge

echo.
pause
