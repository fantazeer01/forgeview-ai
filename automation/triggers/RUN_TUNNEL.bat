@echo off
setlocal

echo ForgeView ngrok Tunnel
echo ======================
echo.

where ngrok >nul 2>nul
if errorlevel 1 (
  echo ERROR: ngrok was not found.
  echo.
  echo Install ngrok with:
  echo winget install ngrok.ngrok
  echo.
  echo After installation, restart this window and run RUN_TUNNEL.bat again.
  echo.
  pause
  exit /b 1
)

echo Starting tunnel for local bridge:
echo http://127.0.0.1:8787
echo.
echo Copy the HTTPS Forwarding URL from ngrok.
echo Use it in n8n as:
echo https://NGROK_URL/forgeview/render-short
echo.

ngrok http 8787

echo.
pause
