# ForgeView Persistent Cloudflare Named Tunnel Setup

Goal: expose the local ForgeView bridge to n8n Cloud with a stable HTTPS URL.

Local bridge:

```text
http://127.0.0.1:8787/forgeview/render-short
```

n8n node to update:

```text
ForgeViewAI Unified Content Machine v8 - 6H
HTTP - Trigger Local Shorts Generator Bridge
```

Required header:

```text
X-ForgeView-Secret: forgeview123
```

## Do You Need A Cloudflare Account?

Yes. A persistent Named Tunnel requires a Cloudflare account.

## Do You Need A Domain?

Recommended: yes.

A stable public HTTPS URL for n8n normally needs a domain connected to Cloudflare DNS, for example:

```text
bridge.yourdomain.com
```

Without a domain, Cloudflare quick tunnels use random `trycloudflare.com` URLs. Those are useful for testing but unstable for automation.

## Recommended Stable URL

Use a subdomain like:

```text
forgeview-bridge.yourdomain.com
```

Then n8n should call:

```text
https://forgeview-bridge.yourdomain.com/forgeview/render-short
```

## Step 1. Install cloudflared

Open Windows PowerShell:

```powershell
winget install Cloudflare.cloudflared
```

Close and reopen PowerShell after installation.

Verify:

```powershell
cloudflared --version
```

## Step 2. Log In To Cloudflare

Run:

```powershell
cloudflared tunnel login
```

This opens a browser.

Choose the Cloudflare account and domain you want to use.

Cloudflare will create a local certificate file under your Windows user profile.

## Step 3. Create A Named Tunnel

Run:

```powershell
cloudflared tunnel create forgeview-local-bridge
```

Cloudflare will print a tunnel ID.

Save that tunnel ID.

## Step 4. Route A Public Hostname To The Tunnel

Replace `forgeview-bridge.yourdomain.com` with your real subdomain:

```powershell
cloudflared tunnel route dns forgeview-local-bridge forgeview-bridge.yourdomain.com
```

This creates the DNS route in Cloudflare.

## Step 5. Create cloudflared Config

Create this folder if it does not exist:

```text
D:\ForgeViewAI\automation\triggers\cloudflared
```

Create:

```text
D:\ForgeViewAI\automation\triggers\cloudflared\config.yml
```

Example:

```yaml
tunnel: forgeview-local-bridge
credentials-file: D:\ForgeViewAI\automation\triggers\cloudflared\YOUR_TUNNEL_ID.json

ingress:
  - hostname: forgeview-bridge.yourdomain.com
    service: http://127.0.0.1:8787
  - service: http_status:404
```

Replace:

```text
YOUR_WINDOWS_USERNAME
YOUR_TUNNEL_ID
forgeview-bridge.yourdomain.com
```

## Step 6. Start ForgeView Bridge First

Double-click:

```text
D:\ForgeViewAI\automation\triggers\RUN_BRIDGE.bat
```

Confirm it shows:

```text
Render endpoint: http://127.0.0.1:8787/forgeview/render-short
```

## Step 7. Start The Named Tunnel

Double-click:

```text
D:\ForgeViewAI\automation\triggers\RUN_NAMED_TUNNEL.bat
```

Or run:

```powershell
cloudflared tunnel run forgeview-local-bridge
```

## Step 8. Test The Public URL

Use PowerShell:

```powershell
$payload = @{
  title = "ForgeView Tunnel Test"
  description = "Testing persistent Cloudflare tunnel."
  scene1 = "Bridge receives request"
  scene2 = "Tunnel stays stable"
  scene3 = "Renderer starts"
  scene4 = "MP4 is created"
  scene5 = "n8n can call local"
  scene6 = "Upload pipeline continues"
  scene7 = "System is ready"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "https://forgeview-bridge.yourdomain.com/forgeview/render-short" `
  -Method POST `
  -Headers @{ "X-ForgeView-Secret" = "forgeview123"; "Content-Type" = "application/json" } `
  -Body $payload `
  -TimeoutSec 1200
```

Expected response:

```json
{
  "ok": true,
  "video_path": "D:\\ForgeViewAI\\output\\media\\videos\\short.mp4",
  "download_url": "http://localhost:8787/files/short.mp4"
}
```

## Step 9. Paste URL Into n8n

In n8n, open:

```text
ForgeViewAI Unified Content Machine v8 - 6H
```

Open node:

```text
HTTP - Trigger Local Shorts Generator Bridge
```

Set URL to:

```text
https://forgeview-bridge.yourdomain.com/forgeview/render-short
```

Keep header:

```text
X-ForgeView-Secret: forgeview123
```

## Important Notes

- Keep `RUN_BRIDGE.bat` running.
- Keep `RUN_NAMED_TUNNEL.bat` running.
- Do not expose Telegram tokens, OpenAI keys, YouTube credentials, or config files.
- The bridge only accepts requests with `X-ForgeView-Secret`.
- For a stronger setup later, rotate the secret and use a longer random value.
