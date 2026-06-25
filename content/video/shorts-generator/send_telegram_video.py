import json
import mimetypes
import sys
import urllib.error
import urllib.request
from pathlib import Path


CONFIG_PATH = Path(r"D:\ForgeViewAI\content\config\telegram_config.json")
VIDEO_PATH = Path(r"D:\ForgeViewAI\output\media\videos\short.mp4")


def load_config(path):
    if not path.exists():
        print("Telegram config missing, video was rendered but not sent")
        return None

    with path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    bot_token = str(config.get("bot_token", "")).strip()
    chat_id = str(config.get("chat_id", "")).strip()

    if not bot_token or not chat_id or bot_token == "PUT_TOKEN_HERE" or chat_id == "PUT_CHAT_ID_HERE":
        print("Telegram config incomplete, video was rendered but not sent")
        return None

    return {"bot_token": bot_token, "chat_id": chat_id}


def multipart_body(fields, files):
    boundary = "forgeview_boundary_telegram_video"
    chunks = []

    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    for field_name, file_path in files.items():
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{file_path.name}"\r\n'
            ).encode("utf-8")
        )
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        chunks.append(file_path.read_bytes())
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), boundary


def send_video(config, video_path):
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    url = f"https://api.telegram.org/bot{config['bot_token']}/sendVideo"
    body, boundary = multipart_body(
        fields={"chat_id": config["chat_id"]},
        files={"video": video_path},
    )
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        status = response.status
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("ok"):
        raise RuntimeError(f"Telegram sendVideo failed: {result}")

    message = result.get("result", {})
    chat = message.get("chat", {})
    print(f"TELEGRAM_HTTP_STATUS={status}")
    print(f"TELEGRAM_API_OK={result.get('ok')}")
    print(f"TELEGRAM_MESSAGE_ID={message.get('message_id', '')}")
    print(f"TELEGRAM_CHAT_ID={chat.get('id', config['chat_id'])}")
    print("Telegram video sent")


def main():
    config = load_config(CONFIG_PATH)
    if config is None:
        return 0

    try:
        send_video(config, VIDEO_PATH)
    except (OSError, urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Telegram send failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
