# ForgeView ngrok Tunnel MVP

This exposes the local ForgeView Shorts Generator Bridge to n8n Cloud for MVP testing.

Local bridge endpoint:

```text
http://127.0.0.1:8787/forgeview/render-short
```

## Install ngrok

If ngrok is not installed, run this in Windows PowerShell:

```powershell
winget install ngrok.ngrok
```

After installation, close and reopen PowerShell or double-click the tunnel launcher again.

## Start Order

1. Start the local bridge first:

```text
D:\ForgeViewAI\automation\triggers\RUN_BRIDGE.bat
```

2. Start the ngrok tunnel second:

```text
D:\ForgeViewAI\automation\triggers\RUN_TUNNEL.bat
```

3. Copy the HTTPS forwarding URL shown by ngrok.

It will look like:

```text
https://example-id.ngrok-free.app
```

4. In n8n, open:

```text
ForgeViewAI Unified Content Machine v8 - 6H
```

5. Edit the node:

```text
HTTP - Trigger Local Shorts Generator Bridge
```

6. Replace the bridge URL with:

```text
https://NGROK_URL/forgeview/render-short
```

Keep the header:

```text
X-ForgeView-Secret: forgeview123
```

## Important

Do not expose bot tokens, OpenAI keys, or YouTube credentials through the tunnel.

This tunnel is for MVP testing only. Keep it running only while testing n8n Cloud.
