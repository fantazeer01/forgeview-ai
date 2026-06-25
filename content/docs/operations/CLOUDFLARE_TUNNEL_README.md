# ForgeView Cloudflare Tunnel MVP

ngrok is blocked, so use a Cloudflare quick tunnel for MVP testing.

Current local bridge:

```text
http://127.0.0.1:8787/forgeview/render-short
```

## Install cloudflared

If `cloudflared` is not installed, run:

```powershell
winget install Cloudflare.cloudflared
```

After installation, close and reopen the terminal or double-click the tunnel launcher again.

## Start Order

1. Start the local bridge first:

```text
D:\ForgeViewAI\automation\triggers\RUN_BRIDGE.bat
```

2. Start the Cloudflare quick tunnel second:

```text
D:\ForgeViewAI\automation\triggers\RUN_CLOUDFLARE_TUNNEL.bat
```

3. Copy the public HTTPS URL shown by Cloudflare.

It should look like:

```text
https://something-random.trycloudflare.com
```

4. In n8n, open:

```text
ForgeViewAI Unified Content Machine v8 - 6H
```

5. Edit this node:

```text
HTTP - Trigger Local Shorts Generator Bridge
```

6. Replace the local bridge URL with:

```text
https://something-random.trycloudflare.com/forgeview/render-short
```

Keep this header:

```text
X-ForgeView-Secret: forgeview123
```

## Notes

This is an MVP quick tunnel. The URL changes every time the tunnel restarts.

Do not expose Telegram bot tokens, OpenAI keys, YouTube credentials, or config files through the tunnel.
