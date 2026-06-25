import json
import socket
import ssl
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PROJECT_ROOT = Path(r"D:\ForgeViewAI")
VIDEO_PATH = PROJECT_ROOT / "output" / "media" / "videos" / "short.mp4"
CONFIG_PATH = PROJECT_ROOT / "content" / "config" / "youtube_upload_config.json"
DEFAULT_CONFIG_EXAMPLE = PROJECT_ROOT / "content" / "config" / "youtube_upload_config.example.json"
TOKEN_PATH = PROJECT_ROOT / "content" / "config" / "youtube_token.json"
SHORTS_GENERATOR_DIR = PROJECT_ROOT / "content" / "video" / "shorts-generator"
EXAMPLE_SHORT_PATH = SHORTS_GENERATOR_DIR / "example_short.json"
VOICE_SCRIPT_PATH = PROJECT_ROOT / "output" / "content" / "shorts-generator" / "voice_script.txt"


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
DEFAULT_TAGS = [
    "ForgeViewAI",
    "AI automation",
    "trading bots",
    "build in public",
    "n8n",
    "Telegram automation",
    "risk management",
    "YouTube Shorts",
]


def require_google_libs():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        print("ERROR: Missing YouTube upload dependencies.")
        print("Install locally with:")
        print("python -m pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
        print(f"Missing import: {exc}")
        return None

    return {
        "Credentials": Credentials,
        "InstalledAppFlow": InstalledAppFlow,
        "Request": Request,
        "build": build,
        "HttpError": HttpError,
        "MediaFileUpload": MediaFileUpload,
    }


def load_json(path):
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_config():
    if not CONFIG_PATH.exists():
        print(f"ERROR: Missing config: {CONFIG_PATH}")
        print(f"Create it from: {DEFAULT_CONFIG_EXAMPLE}")
        return None

    config = load_json(CONFIG_PATH)
    config.setdefault("privacy_status", "private")
    config.setdefault("channel_handle", "@ForgeViewGrowth")
    return config


def load_short_context():
    if EXAMPLE_SHORT_PATH.exists():
        return load_json(EXAMPLE_SHORT_PATH)

    return {
        "title": "The Bot Bug That Traps Trades",
        "description": "A ForgeViewAI build-in-public lesson about trading bot reliability.",
    }


def build_description(short_context):
    base = str(short_context.get("description", "")).strip()
    if not base:
        base = "A ForgeViewAI build-in-public lesson about AI automation, trading bots, and workflow reliability."

    voice_summary = ""
    if VOICE_SCRIPT_PATH.exists():
        lines = [line.strip() for line in VOICE_SCRIPT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            voice_summary = "\n\nNarration:\n" + "\n".join(lines[:7])

    return (
        f"{base}{voice_summary}\n\n"
        "#Shorts\n\n"
        "Follow ForgeView:\n\n"
        "Telegram:\n"
        "https://t.me/ForgeViewCom\n\n"
        "X:\n"
        "https://x.com/ForgeViewX\n\n"
        "Building AI automation systems, trading bots, and workflows in public."
    )


def build_metadata(config):
    short_context = load_short_context()
    title = str(short_context.get("title", "ForgeViewAI Automation Short")).strip()
    if "#Shorts" not in title:
        title = f"{title} #Shorts"
    title = title[:100]

    privacy_status = str(config.get("privacy_status", "private")).strip().lower()
    if privacy_status != "private":
        print("WARNING: First upload should be private. Forcing privacy_status to private.")
        privacy_status = "private"

    return {
        "snippet": {
            "title": title,
            "description": build_description(short_context),
            "tags": DEFAULT_TAGS,
            "categoryId": "28",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }


def extract_authorization_code(value):
    value = str(value or "").strip()
    if not value:
        return ""

    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        query = parse_qs(parsed.query)
        code = query.get("code", [""])[0]
        return code.strip()

    return value


def run_manual_oauth_flow(client_secret_path, libs):
    InstalledAppFlow = libs["InstalledAppFlow"]

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
    flow.redirect_uri = "http://localhost"
    authorization_url, _state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    print("")
    print("MANUAL_OAUTH_REQUIRED=True")
    print("Open this authorization URL in your browser:")
    print(authorization_url)
    print("")
    print("After approving access, Google will redirect to a localhost URL that may fail to load.")
    print("Copy the full redirected URL from the browser address bar, or copy only the code= value.")
    pasted = input("Paste redirected URL or authorization code here: ").strip()
    code = extract_authorization_code(pasted)

    if not code:
        raise RuntimeError("No authorization code found in pasted input.")

    flow.fetch_token(code=code)
    return flow.credentials


def get_authenticated_service(config, libs):
    client_secret_path = Path(str(config.get("client_secret_path", "")).strip())
    if not client_secret_path.exists():
        raise FileNotFoundError(f"client_secret_path not found: {client_secret_path}")

    Credentials = libs["Credentials"]
    InstalledAppFlow = libs["InstalledAppFlow"]
    Request = libs["Request"]
    build = libs["build"]

    creds = None
    reused_existing_token = False
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        reused_existing_token = bool(creds and creds.valid)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                reused_existing_token = True
            except Exception as exc:
                print(f"TOKEN_REFRESH_FAILED={type(exc).__name__}: {exc}")
                creds = run_manual_oauth_flow(client_secret_path, libs)
        else:
            creds = run_manual_oauth_flow(client_secret_path, libs)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        print(f"TOKEN_SAVED=True")
        print(f"TOKEN_PATH={TOKEN_PATH}")

    print(f"EXISTING_TOKEN_REUSED={reused_existing_token}")
    return build("youtube", "v3", credentials=creds), reused_existing_token


def upload_video(youtube, metadata, libs):
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"Video not found: {VIDEO_PATH}")

    MediaFileUpload = libs["MediaFileUpload"]
    HttpError = libs["HttpError"]
    media = MediaFileUpload(
        str(VIDEO_PATH),
        chunksize=1 * 1024 * 1024,
        resumable=True,
        mimetype="video/mp4",
    )
    request = youtube.videos().insert(
        part="snippet,status",
        body=metadata,
        media_body=media,
    )

    response = None
    retry_count = 0
    max_retries = 5
    last_progress = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                last_progress = max(last_progress, int(status.progress() * 100))
                print(f"Upload progress: {last_progress}%")
            retry_count = 0
        except (HttpError, ConnectionResetError, socket.error, ssl.SSLError) as exc:
            retry_count += 1
            if retry_count > max_retries:
                raise RuntimeError(
                    f"Upload failed after {max_retries} retries. "
                    f"Last progress: {last_progress}%. "
                    f"Final error: {type(exc).__name__}: {exc}"
                ) from exc

            wait_seconds = min(60, 2 ** retry_count)
            print(f"Upload retry {retry_count}/{max_retries} after {type(exc).__name__}: {exc}")
            print(f"Waiting {wait_seconds}s before retry...")
            time.sleep(wait_seconds)

    print("Upload progress: 100%")
    return response, max(last_progress, 100)


def main():
    config = load_config()
    if config is None:
        return 1

    metadata = build_metadata(config)
    print("Generated YouTube metadata:")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))

    libs = require_google_libs()
    if libs is None:
        return 1

    reused_existing_token = TOKEN_PATH.exists()
    try:
        youtube, reused_existing_token = get_authenticated_service(config, libs)
        response, progress = upload_video(youtube, metadata, libs)
    except Exception as exc:
        print("UPLOAD_SUCCESS=False")
        print(f"EXISTING_TOKEN_REUSED={reused_existing_token}")
        print("UPLOAD_PROGRESS_REACHED=unknown")
        print("VIDEO_ID=none")
        print("VIDEO_URL=none")
        print(f"PRIVACY_STATUS={metadata['status']['privacyStatus']}")
        print(f"ERROR: YouTube upload failed: {exc}")
        return 1

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    print("UPLOAD_SUCCESS=True")
    print(f"EXISTING_TOKEN_REUSED={reused_existing_token}")
    print(f"UPLOAD_PROGRESS_REACHED={progress}%")
    print(f"VIDEO_ID={video_id}")
    print(f"VIDEO_URL={video_url}")
    print(f"PRIVACY_STATUS={metadata['status']['privacyStatus']}")
    print(f"TITLE={metadata['snippet']['title']}")
    print("DESCRIPTION=")
    print(metadata["snippet"]["description"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
