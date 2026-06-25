@echo off
setlocal

echo ForgeView Cloudflare Tunnel
echo ===========================
echo.

where cloudflared >nul 2>nul
if errorlevel 1 (
  echo ERROR: cloudflared was not found.
  echo.
  echo Install Cloudflare Tunnel with:
  echo winget install Cloudflare.cloudflared
  echo.
  echo After installation, restart this window and run RUN_CLOUDFLARE_TUNNEL.bat again.
  echo.
  pause
  exit /b 1
)

echo Starting quick tunnel for local bridge:
echo http://127.0.0.1:8787
echo.
echo Copy the public HTTPS trycloudflare.com URL from the output.
echo Use it in n8n as:
echo https://YOUR-URL.trycloudflare.com/forgeview/render-short
echo.

cloudflared tunnel --protocol http2 --url http://127.0.0.1:8787

echo.
pause
