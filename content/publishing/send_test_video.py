import json
import mimetypes
import sys
import urllib.error
import urllib.request
from pathlib import Path


CONFIG_PATH = Path(r"D:\ForgeViewAI\content\config\telegram_config.json")
VIDEO_PATH = Path(r"D:\ForgeViewAI\output\media\videos\short.mp4")


def build_multipart(fields, files):
    boundary = "forgeview_send_test_video_boundary"
    chunks = []

    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    for name, path in files.items():
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode("utf-8")
        )
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), boundary


def main():
    if not CONFIG_PATH.exists():
        print("HTTP status: none")
        print("Telegram response: config file missing")
        print("Message ID: none")
        return 1

    if not VIDEO_PATH.exists():
        print("HTTP status: none")
        print("Telegram response: video file missing")
        print("Message ID: none")
        return 1

    with CONFIG_PATH.open("r", encoding="utf-8-sig") as f:
        config = json.load(f)

    bot_token = str(config.get("bot_token", "")).strip()
    chat_id = str(config.get("chat_id", "")).strip()

    if not bot_token or not chat_id:
        print("HTTP status: none")
        print("Telegram response: bot_token or chat_id missing")
        print("Message ID: none")
        return 1

    body, boundary = build_multipart({"chat_id": chat_id}, {"video": VIDEO_PATH})
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/sendVideo",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            status = response.status
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print("HTTP status: none")
        print(f"Telegram response: {type(exc).__name__}: {exc}")
        print("Message ID: none")
        return 1

    message_id = "none"
    try:
        parsed = json.loads(raw)
        message_id = str(parsed.get("result", {}).get("message_id", "none"))
    except json.JSONDecodeError:
        pass

    print(f"HTTP status: {status}")
    print(f"Telegram response: {raw}")
    print(f"Message ID: {message_id}")

    return 0 if status == 200 and message_id != "none" else 1


if __name__ == "__main__":
    sys.exit(main())
