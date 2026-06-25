import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import urllib.error
import urllib.request


PROJECT_ROOT = Path(r"D:\ForgeViewAI")
CONFIG_PATH = PROJECT_ROOT / "content" / "config" / "bridge_config.json"
VIDEO_PROVIDER_CONFIG_PATH = PROJECT_ROOT / "content" / "config" / "video_provider_config.json"
LOG_PATH = PROJECT_ROOT / "state" / "logs" / "bridge_runtime.log"
GENERATOR_DIR = PROJECT_ROOT / "content" / "video" / "shorts-generator"
GENERATOR_OUTPUT_DIR = PROJECT_ROOT / "output" / "content" / "shorts-generator"
INPUT_PATH = GENERATOR_OUTPUT_DIR / "input_from_n8n.json"
OUTPUT_PATH = PROJECT_ROOT / "output" / "media" / "videos" / "short.mp4"
OPENAI_CONFIG_PATH = PROJECT_ROOT / "content" / "config" / "openai_config.json"
DEFAULT_MUSIC_PATH = PROJECT_ROOT / "output" / "media" / "videos" / "background.mp3"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
SCENE_KEYS = [f"scene{i}" for i in range(1, 8)]
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"
OPENAI_TTS_VOICE = "alloy"
DEFAULT_VIDEO_PROVIDER_CONFIG = {
    "video_provider": "local_image_slideshow",
    "fallback_provider": "local_image_slideshow",
    "publish_mode": "draft_only",
    "kling_preview_mode": True,
    "kling_access_key": "",
    "kling_secret_key": "",
    "kling_base_url": "",
    "kling_model_name": "kling-v3-0",
    "clip_duration_seconds": 4,
    "scene_count": 7,
    "aspect_ratio": "9:16",
    "resolution": "1080x1920",
    "max_estimated_cost_usd": 3.0,
}
KLING_COST_PER_SECOND_USD = 0.084
KLING_CREATE_PATH = "/v1/videos/text2video"
KLING_QUERY_PATH = "/v1/videos/text2video/{task_id}"
KLING_TASK_TIMEOUT_SECONDS = 1800
KLING_POLL_SECONDS = 10
MIN_KLING_SCENES_FOR_FALLBACK = 5


class BridgeRenderError(RuntimeError):
    def __init__(self, error, stage, details="", **fields):
        super().__init__(error)
        self.error = error
        self.stage = stage
        self.details = details
        self.fields = fields

    def to_payload(self):
        payload = {
            "ok": False,
            "error": self.error,
            "stage": self.stage,
            "details": self.details,
        }
        payload.update(self.fields)
        return payload


def log_runtime_event(event, **fields):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "event": event,
        **fields,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing bridge config: {CONFIG_PATH}. Copy bridge_config.example.json to bridge_config.json and set a secret."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)

    secret = str(config.get("secret", "")).strip()
    if not secret or secret == "CHANGE_ME_LOCAL_SECRET":
        raise ValueError("bridge_config.json must contain a non-placeholder secret.")

    host = str(config.get("host") or DEFAULT_HOST).strip()
    port = int(config.get("port") or DEFAULT_PORT)
    return {"secret": secret, "host": host, "port": port}


def load_video_provider_config():
    if not VIDEO_PROVIDER_CONFIG_PATH.exists():
        return dict(DEFAULT_VIDEO_PROVIDER_CONFIG)

    with VIDEO_PROVIDER_CONFIG_PATH.open("r", encoding="utf-8-sig") as f:
        config = json.load(f)

    merged = dict(DEFAULT_VIDEO_PROVIDER_CONFIG)
    merged.update(config)
    if not str(merged.get("kling_access_key", "")).strip() or str(merged.get("kling_access_key", "")).strip() == "PASTE_ACCESS_KEY_HERE":
        merged["kling_access_key"] = os.environ.get("KLING_ACCESS_KEY", "").strip() or merged.get("kling_access_key", "")
    if not str(merged.get("kling_secret_key", "")).strip() or str(merged.get("kling_secret_key", "")).strip() == "PASTE_SECRET_KEY_HERE":
        merged["kling_secret_key"] = os.environ.get("KLING_SECRET_KEY", "").strip() or merged.get("kling_secret_key", "")
    return merged


def is_placeholder_secret(value, placeholder):
    value = str(value or "").strip()
    return not value or value == placeholder


def estimate_kling_cost(config):
    scene_count = int(config.get("scene_count") or len(SCENE_KEYS))
    clip_duration = float(config.get("clip_duration_seconds") or 4)
    return round(scene_count * clip_duration * KLING_COST_PER_SECOND_USD, 3)


def resolve_video_provider(config):
    provider = str(config.get("video_provider") or "local_image_slideshow").strip()
    fallback = str(config.get("fallback_provider") or "").strip()
    warnings = []

    if provider == "local_image_slideshow":
        return provider, warnings

    if provider == "kling_text_to_video":
        estimated_cost = estimate_kling_cost(config)
        max_cost = float(config.get("max_estimated_cost_usd") or 0)
        if max_cost > 0 and estimated_cost > max_cost:
            raise RuntimeError("KLING COST LIMIT EXCEEDED")

        has_kling_config = (
            not is_placeholder_secret(config.get("kling_access_key"), "PASTE_ACCESS_KEY_HERE")
            and not is_placeholder_secret(config.get("kling_secret_key"), "PASTE_SECRET_KEY_HERE")
            and bool(str(config.get("kling_base_url") or "").strip())
        )
        if fallback == "local_image_slideshow":
            if not has_kling_config:
                warnings.append("KLING API NOT CONFIGURED; used local_image_slideshow fallback")
                return fallback, warnings
        if not has_kling_config:
            raise RuntimeError("KLING API NOT CONFIGURED")
        return provider, warnings

    if provider in {"runway_text_to_video", "pixverse_text_to_video"}:
        if fallback == "local_image_slideshow":
            warnings.append(f"{provider} is a future provider placeholder; used local_image_slideshow fallback")
            return fallback, warnings

        raise RuntimeError(f"{provider.upper()} NOT CONFIGURED")

    raise RuntimeError(f"Unsupported video_provider: {provider}")


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def build_kling_jwt(access_key, secret_key):
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"iss": access_key, "exp": now + 1800, "nbf": now - 5}
    signing_input = f"{b64url(json.dumps(header, separators=(',', ':')).encode('utf-8'))}.{b64url(json.dumps(payload, separators=(',', ':')).encode('utf-8'))}"
    signature = hmac.new(secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{b64url(signature)}"


def kling_request(config, method, path, body=None):
    base_url = str(config.get("kling_base_url") or "").rstrip("/")
    if not base_url:
        raise RuntimeError("KLING API NOT CONFIGURED")

    token = build_kling_jwt(str(config["kling_access_key"]), str(config["kling_secret_key"]))
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code in (401, 403):
            raise RuntimeError("KLING AUTH FAILED") from exc
        raise RuntimeError(f"KLING API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"KLING API NETWORK ERROR: {exc.reason}") from exc


def build_kling_prompts(payload, config):
    configured_prompts = payload.get("video_prompts")
    if isinstance(configured_prompts, list) and len(configured_prompts) >= len(SCENE_KEYS):
        return [str(p).strip() for p in configured_prompts[: len(SCENE_KEYS)]]

    prompts = []
    for index, key in enumerate(SCENE_KEYS, start=1):
        scene = str(payload.get(key) or f"Scene {index}").strip()
        prompts.append(
            "Vertical 9:16 AI video for ForgeViewAI. "
            f"Scene {index}: {scene}. "
            "Dark charcoal and black visual identity, yellow ForgeView accent lighting, anonymous founder protagonist, "
            "AI automation and trading-system reliability mood, cinematic motion, strong foreground subject, "
            "clear background environment, no readable text, no letters, no logos, no watermarks, no UI screenshots."
        )
    return prompts


def extract_kling_task_id(response):
    candidates = [
        response.get("task_id"),
        response.get("id"),
        response.get("data", {}).get("task_id") if isinstance(response.get("data"), dict) else None,
        response.get("data", {}).get("id") if isinstance(response.get("data"), dict) else None,
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    raise RuntimeError("KLING TASK CREATE FAILED")


def extract_kling_status(response):
    data = response.get("data") if isinstance(response.get("data"), dict) else response
    status = str(data.get("task_status") or data.get("status") or "").lower()
    if status in {"succeed", "succeeded", "success", "completed", "complete"}:
        return "succeeded"
    if status in {"failed", "fail", "error"}:
        return "failed"
    return "running"


def extract_kling_video_url(response):
    data = response.get("data") if isinstance(response.get("data"), dict) else response
    works = data.get("task_result", {}).get("videos") if isinstance(data.get("task_result"), dict) else None
    if isinstance(works, list) and works:
        for item in works:
            if isinstance(item, dict) and item.get("url"):
                return item["url"]
    for key in ("video_url", "url", "download_url"):
        if data.get(key):
            return data[key]
    raise RuntimeError("KLING TASK FAILED")


def create_kling_task(config, prompt, index):
    payload = {
        "model_name": str(config.get("kling_model_name") or "kling-v3-0"),
        "prompt": prompt,
        "negative_prompt": "text, letters, words, logos, watermarks, UI screenshots, readable symbols, captions",
        "cfg_scale": 0.5,
        "mode": "std",
        "duration": int(config.get("clip_duration_seconds") or 4),
        "aspect_ratio": str(config.get("aspect_ratio") or "9:16"),
        "external_task_id": f"forgeview-scene-{index}-{int(time.time())}",
    }
    try:
        response = kling_request(config, "POST", KLING_CREATE_PATH, payload)
        return extract_kling_task_id(response)
    except RuntimeError as exc:
        raise RuntimeError(f"KLING TASK CREATE FAILED: {exc}") from exc


def poll_kling_task(config, task_id):
    deadline = time.time() + KLING_TASK_TIMEOUT_SECONDS
    while time.time() < deadline:
        response = kling_request(config, "GET", KLING_QUERY_PATH.format(task_id=task_id))
        status = extract_kling_status(response)
        if status == "succeeded":
            return extract_kling_video_url(response)
        if status == "failed":
            raise RuntimeError("KLING TASK FAILED")
        time.sleep(KLING_POLL_SECONDS)
    raise RuntimeError("KLING TASK TIMEOUT")


def download_kling_clip(url, path):
    request = urllib.request.Request(url, headers={"User-Agent": "ForgeViewAI/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.read())
    except Exception as exc:
        raise RuntimeError("KLING CLIP DOWNLOAD FAILED") from exc

    if not path.exists() or path.stat().st_size <= 0:
        raise RuntimeError("KLING CLIP DOWNLOAD FAILED")


def load_openai_api_key():
    if not OPENAI_CONFIG_PATH.exists():
        return ""
    try:
        with OPENAI_CONFIG_PATH.open("r", encoding="utf-8-sig") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        return ""
    api_key = str(config.get("api_key", "")).strip()
    if not api_key or api_key == "PUT_API_KEY_HERE":
        return ""
    return api_key


def normalize_scene_narrations(payload):
    assembled_scene_narrations = payload.get("assembled_scene_narrations")
    if isinstance(assembled_scene_narrations, list) and assembled_scene_narrations:
        return [str(line).strip() for line in assembled_scene_narrations if str(line).strip()]

    scenes = [str(payload.get(key) or "").strip() for key in SCENE_KEYS]
    scene_narrations = payload.get("scene_narrations")
    if isinstance(scene_narrations, list) and len(scene_narrations) >= len(SCENE_KEYS):
        return [str(line).strip() for line in scene_narrations[: len(SCENE_KEYS)]]

    narration_script = str(payload.get("narration_script") or "").strip()
    if narration_script:
        lines = [line.strip() for line in narration_script.splitlines() if line.strip()]
        if len(lines) >= len(SCENE_KEYS):
            return lines[: len(SCENE_KEYS)]

    return [
        scene if scene else f"Scene {index}: ForgeView automation lesson."
        for index, scene in enumerate(scenes, start=1)
    ]


def srt_time(seconds):
    millis = int(round(seconds * 1000))
    hours = millis // 3_600_000
    millis %= 3_600_000
    minutes = millis // 60_000
    millis %= 60_000
    secs = millis // 1000
    millis %= 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def write_subtitles(path, scene_narrations, scene_seconds):
    blocks = []
    for index, line in enumerate(scene_narrations, start=1):
        start = (index - 1) * scene_seconds
        end = index * scene_seconds - 0.15
        wrapped = "\n".join(textwrap.wrap(line, width=34)[:2])
        blocks.append(f"{index}\n{srt_time(start)} --> {srt_time(end)}\n{wrapped}\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(blocks), encoding="utf-8")


def write_caption_textfiles(caption_dir, scene_narrations):
    caption_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, line in enumerate(scene_narrations, start=1):
        caption = "\n".join(textwrap.wrap(line, width=30)[:2])
        path = caption_dir / f"caption{index}.txt"
        path.write_text(caption, encoding="utf-8")
        paths.append(path)
    return paths


def generate_tts(path, narration_text, api_key):
    if not api_key:
        return False
    payload = {
        "model": OPENAI_TTS_MODEL,
        "voice": OPENAI_TTS_VOICE,
        "input": narration_text,
        "response_format": "mp3",
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())
    return path.exists() and path.stat().st_size > 0


def generate_builtin_music(path, duration):
    sample_rate = 44100
    bpm = 112
    beat_interval = 60.0 / bpm
    total_samples = int(duration * sample_rate)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            beat_phase = (t % beat_interval) / beat_interval
            kick = max(0.0, 1.0 - beat_phase * 9.0)
            pulse = 0.45 if beat_phase < 0.08 else 0.0
            bass = math_sin(55.0, t) * (0.32 + pulse) + math_sin(110.0, t) * 0.09
            texture = math_sin(220.0, t) * 0.025
            sample = int(max(-1, min(1, bass * kick + texture)) * 32767)
            frames.extend(sample.to_bytes(2, byteorder="little", signed=True))
        wav.writeframes(bytes(frames))
    return path


def math_sin(freq, t):
    import math

    return math.sin(2 * math.pi * freq * t)


def ffmpeg_filter_path(path):
    return str(path).replace("\\", "/").replace(":", "\\:")


def build_caption_filter(caption_paths, scene_seconds):
    filters = [
        "scale=1080:1920:force_original_aspect_ratio=decrease",
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "setsar=1",
    ]
    font = ffmpeg_filter_path(Path(r"C:\Windows\Fonts\arial.ttf"))
    for index, caption_path in enumerate(caption_paths, start=1):
        start = (index - 1) * scene_seconds
        end = index * scene_seconds
        textfile = ffmpeg_filter_path(caption_path)
        filters.append(
            "drawbox=x=64:y=1510:w=952:h=230:color=black@0.62:t=fill:"
            f"enable='between(t,{start:.3f},{end:.3f})'"
        )
        filters.append(
            f"drawtext=fontfile='{font}':textfile='{textfile}':"
            "fontcolor=white:fontsize=48:line_spacing=10:"
            "x=(w-text_w)/2:y=1585:shadowcolor=black@0.85:shadowx=3:shadowy=3:"
            f"enable='between(t,{start:.3f},{end:.3f})'"
        )
        filters.append(
            f"drawtext=fontfile='{font}':text='ForgeViewAI':fontcolor=yellow:fontsize=34:"
            f"x=48:y=48:shadowcolor=black@0.75:shadowx=2:shadowy=2:"
            f"enable='between(t,{start:.3f},{end:.3f})'"
        )
    return ",".join(filters)


def assemble_kling_clips(clip_paths, output_path, payload, provider_config):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg not found in PATH. Install FFmpeg and restart the terminal.")

    concat_path = GENERATOR_OUTPUT_DIR / "work" / "kling_clips" / "concat.txt"
    work_dir = GENERATOR_OUTPUT_DIR / "work" / "kling_cinematic"
    temp_video = work_dir / "kling_concat_raw.mp4"
    audio_dir = work_dir / "audio"
    caption_dir = work_dir / "captions"
    subtitles_path = work_dir / "subtitles.srt"
    narration_path = audio_dir / "narration.mp3"
    concat_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    concat_lines = []
    for path in clip_paths:
        safe_path = str(path).replace("'", "'\\''")
        concat_lines.append(f"file '{safe_path}'")
    concat_path.write_text("\n".join(concat_lines), encoding="utf-8")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_command = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-c",
        "copy",
        str(temp_video),
    ]
    log_runtime_event("ffmpeg concat started", clip_count=len(clip_paths), output=str(temp_video))
    concat_result = subprocess.run(concat_command, cwd=str(GENERATOR_DIR), capture_output=True, text=True, timeout=1800)
    if concat_result.returncode != 0:
        log_runtime_event("ffmpeg concat fail", returncode=concat_result.returncode, stderr=concat_result.stderr[-2000:])
        raise BridgeRenderError(
            "FFMPEG CONCAT FAILED",
            "ffmpeg_concat",
            "Kling clip concat failed.",
            returncode=concat_result.returncode,
            stderr=concat_result.stderr[-2000:],
            stdout=concat_result.stdout[-2000:],
        )
    log_runtime_event("ffmpeg concat success", output=str(temp_video))

    scene_seconds = float(provider_config.get("clip_duration_seconds") or 5)
    duration = scene_seconds * len(clip_paths)
    scene_narrations = normalize_scene_narrations(payload)
    write_subtitles(subtitles_path, scene_narrations, scene_seconds)
    caption_paths = write_caption_textfiles(caption_dir, scene_narrations)
    openai_key = load_openai_api_key()
    narration_used = generate_tts(narration_path, " ".join(scene_narrations), openai_key)
    music_path = DEFAULT_MUSIC_PATH if DEFAULT_MUSIC_PATH.exists() else generate_builtin_music(audio_dir / "builtin_dark_tech_beat.wav", duration)
    caption_filter = build_caption_filter(caption_paths, scene_seconds)

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(temp_video),
    ]
    if narration_used:
        command.extend(["-i", str(narration_path)])
    if music_path and Path(music_path).exists():
        command.extend(["-stream_loop", "-1", "-i", str(music_path)])

    command.extend([
        "-vf",
        caption_filter,
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
    ])

    audio_inputs = int(narration_used) + int(bool(music_path and Path(music_path).exists()))
    if narration_used and music_path and Path(music_path).exists():
        command.extend([
            "-filter_complex",
            f"[1:a]volume=1.0,apad,atrim=0:{duration:.3f}[voice];"
            f"[2:a]volume=0.22,atrim=0:{duration:.3f}[music];"
            "[voice][music]amix=inputs=2:duration=longest:normalize=0[aout]",
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
        ])
    elif narration_used:
        command.extend([
            "-filter_complex",
            f"[1:a]volume=1.0,apad,atrim=0:{duration:.3f}[aout]",
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
        ])
    elif music_path and Path(music_path).exists():
        command.extend([
            "-filter_complex",
            f"[1:a]volume=0.22,atrim=0:{duration:.3f}[aout]",
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
        ])
    else:
        command.extend(["-an"])

    command.extend(["-t", f"{duration:.3f}", "-shortest", str(output_path)])
    log_runtime_event("ffmpeg assembly started", clip_count=len(clip_paths), output=str(output_path), duration_seconds=duration)
    result = subprocess.run(command, cwd=str(GENERATOR_DIR), capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        log_runtime_event("ffmpeg assembly fail", returncode=result.returncode, stderr=result.stderr[-2000:])
        raise BridgeRenderError(
            "FFMPEG ASSEMBLY FAILED",
            "ffmpeg_assembly",
            "Kling cinematic final assembly failed.",
            returncode=result.returncode,
            stderr=result.stderr[-2000:],
            stdout=result.stdout[-2000:],
        )

    if not output_path.exists():
        log_runtime_event("ffmpeg assembly fail", error="SHORT MP4 NOT FOUND", output=str(output_path))
        raise BridgeRenderError(
            "SHORT MP4 NOT FOUND",
            "ffmpeg_assembly",
            f"Render completed but output MP4 was not found: {output_path}",
        )
    log_runtime_event("ffmpeg assembly success", output=str(output_path), size_bytes=output_path.stat().st_size)

    return {
        "narration_used": narration_used,
        "background_music_used": bool(music_path and Path(music_path).exists()),
        "subtitles_burned_in": True,
        "subtitle_path": str(subtitles_path),
        "narration_audio_path": str(narration_path) if narration_used else "",
        "music_path": str(music_path) if music_path else "",
    }


def render_kling_short(payload, provider_config):
    estimated_cost = estimate_kling_cost(provider_config)
    max_cost = float(provider_config.get("max_estimated_cost_usd") or 0)
    if max_cost > 0 and estimated_cost > max_cost:
        raise RuntimeError("KLING COST LIMIT EXCEEDED")

    prompts = build_kling_prompts(payload, provider_config)
    clip_dir = GENERATOR_OUTPUT_DIR / "work" / "kling_clips"
    clip_dir.mkdir(parents=True, exist_ok=True)
    (clip_dir / "video_prompts.json").write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")

    clip_paths = []
    task_ids = []
    failed_scenes = []
    successful_scene_narrations = []
    all_scene_narrations = normalize_scene_narrations(payload)
    for index, prompt in enumerate(prompts, start=1):
        clip_path = clip_dir / f"scene{index}.mp4"
        if clip_path.exists():
            clip_path.unlink()
        log_runtime_event("scene started", scene=index, provider="kling_text_to_video")
        try:
            task_id = create_kling_task(provider_config, prompt, index)
            task_ids.append(task_id)
            video_url = poll_kling_task(provider_config, task_id)
            download_kling_clip(video_url, clip_path)
            clip_paths.append(clip_path)
            narration_index = index - 1
            if narration_index < len(all_scene_narrations):
                successful_scene_narrations.append(all_scene_narrations[narration_index])
            else:
                successful_scene_narrations.append(f"Scene {index}: ForgeView automation lesson.")
            log_runtime_event("scene success", scene=index, task_id=task_id, clip_path=str(clip_path), size_bytes=clip_path.stat().st_size)
        except Exception as exc:
            error_text = str(exc) or exc.__class__.__name__
            if error_text.startswith("KLING AUTH FAILED"):
                log_runtime_event("scene failed", scene=index, error=error_text, fatal=True)
                raise
            failed_scenes.append({
                "scene": index,
                "stage": f"scene_{index}_generation",
                "error": error_text,
                "type": exc.__class__.__name__,
            })
            log_runtime_event(
                "scene failed",
                scene=index,
                stage=f"scene_{index}_generation",
                error=error_text,
                error_type=exc.__class__.__name__,
                fatal=False,
            )
            log_runtime_event("scene skipped", scene=index, stage=f"scene_{index}_generation", reason="kling scene generation failed")
            continue

    if len(clip_paths) < MIN_KLING_SCENES_FOR_FALLBACK:
        log_runtime_event(
            "kling fallback fail",
            successful_scenes=len(clip_paths),
            required_minimum=MIN_KLING_SCENES_FOR_FALLBACK,
            failed_scenes=failed_scenes,
        )
        raise BridgeRenderError(
            "KLING SCENE FALLBACK FAILED",
            "scene_generation",
            f"Only {len(clip_paths)} new scenes generated; minimum required is {MIN_KLING_SCENES_FOR_FALLBACK}.",
            successful_scenes=len(clip_paths),
            required_minimum=MIN_KLING_SCENES_FOR_FALLBACK,
            failed_scenes=failed_scenes,
        )

    assembly_payload = dict(payload)
    assembly_payload["assembled_scene_narrations"] = successful_scene_narrations
    if failed_scenes:
        log_runtime_event(
            "kling fallback active",
            successful_scene_count=len(clip_paths),
            failed_scenes=failed_scenes,
        )

    media_result = assemble_kling_clips(clip_paths, OUTPUT_PATH, assembly_payload, provider_config)
    return {
        "active_video_provider": "kling_text_to_video",
        "configured_video_provider": provider_config.get("video_provider", "kling_text_to_video"),
        "provider_warnings": [
            f"Skipped scene {item['scene']}: {item['error']}" for item in failed_scenes
        ],
        "estimated_cost_usd": estimated_cost,
        "kling_task_ids": task_ids,
        "kling_clip_paths": [str(path) for path in clip_paths],
        "kling_failed_scenes": failed_scenes,
        **media_result,
        "size_bytes": OUTPUT_PATH.stat().st_size,
    }


def find_python():
    venv_python = GENERATOR_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)

    for candidate in ("py", "python"):
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return candidate
        except (OSError, subprocess.SubprocessError):
            continue

    raise RuntimeError("Python was not found. Install Python or create the Shorts Generator .venv.")


def validate_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    missing = [key for key in ["title", "description"] if not str(payload.get(key, "")).strip()]
    if missing:
        raise ValueError(f"Missing required Shorts JSON fields: {', '.join(missing)}")

    cleaned = {
        "title": str(payload["title"]).strip(),
        "description": str(payload["description"]).strip(),
    }
    scene_narrations = payload.get("scene_narrations")
    for key in SCENE_KEYS:
        value = str(payload.get(key, "")).strip()
        if not value and isinstance(scene_narrations, list):
            index = int(key.replace("scene", "")) - 1
            value = " ".join(str(scene_narrations[index]).split()[:6]) if index < len(scene_narrations) else ""
        cleaned[key] = value or key
    if isinstance(payload.get("video_prompts"), list):
        cleaned["video_prompts"] = payload["video_prompts"]
    if isinstance(payload.get("scene_narrations"), list):
        cleaned["scene_narrations"] = payload["scene_narrations"]
    if str(payload.get("narration_script", "")).strip():
        cleaned["narration_script"] = str(payload["narration_script"]).strip()
    if isinstance(payload.get("tags"), list):
        cleaned["tags"] = payload["tags"]
    return cleaned


def render_short(payload):
    provider_config = load_video_provider_config()
    active_provider, provider_warnings = resolve_video_provider(provider_config)

    if active_provider == "kling_text_to_video":
        started = time.time()
        result = render_kling_short(payload, provider_config)
        if not OUTPUT_PATH.exists():
            raise RuntimeError("SHORT MP4 NOT FOUND")
        result["duration_seconds"] = round(time.time() - started, 2)
        result["publish_mode"] = provider_config.get("publish_mode", "draft_only")
        result["kling_preview_mode"] = bool(provider_config.get("kling_preview_mode", True))
        return result

    if active_provider != "local_image_slideshow":
        raise RuntimeError(f"Unsupported active provider: {active_provider}")

    GENERATOR_DIR.mkdir(parents=True, exist_ok=True)
    GENERATOR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with INPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    python_cmd = find_python()
    command = [
        python_cmd,
        str(GENERATOR_DIR / "render_short.py"),
        "--input",
        str(INPUT_PATH),
        "--output",
        str(OUTPUT_PATH),
        "--workdir",
        str(GENERATOR_OUTPUT_DIR / "work"),
    ]

    started = time.time()
    result = subprocess.run(
        command,
        cwd=str(GENERATOR_DIR),
        capture_output=True,
        text=True,
        timeout=1800,
    )
    duration = round(time.time() - started, 2)

    if result.returncode != 0:
        raise RuntimeError(
            "Shorts render failed.\n"
            f"Exit code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    if not OUTPUT_PATH.exists():
        raise RuntimeError(f"Render completed but output MP4 was not found: {OUTPUT_PATH}")

    return {
        "active_video_provider": active_provider,
        "configured_video_provider": provider_config.get("video_provider", "local_image_slideshow"),
        "provider_warnings": provider_warnings,
        "estimated_cost_usd": estimate_kling_cost(provider_config),
        "publish_mode": provider_config.get("publish_mode", "draft_only"),
        "kling_preview_mode": bool(provider_config.get("kling_preview_mode", True)),
        "duration_seconds": duration,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "size_bytes": OUTPUT_PATH.stat().st_size,
    }


class ForgeViewBridgeHandler(BaseHTTPRequestHandler):
    config = None

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {self.address_string()} {fmt % args}")

    def write_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def require_secret(self):
        provided = self.headers.get("X-ForgeView-Secret", "")
        return provided == self.config["secret"]

    def do_POST(self):
        stage = "payload_validation"
        try:
            parsed = urlparse(self.path)
            if parsed.path != "/forgeview/render-short":
                self.write_json(404, {"ok": False, "error": "Not found"})
                return

            if not self.require_secret():
                self.write_json(401, {"ok": False, "error": "Missing or invalid X-ForgeView-Secret header"})
                return

            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            shorts_json = payload.get("shorts_json", payload)
            cleaned = validate_payload(shorts_json)
            stage = "scene_generation"
            render_result = render_short(cleaned)
            port = self.server.server_address[1]
            self.write_json(
                200,
                {
                    "ok": True,
                    "video_path": str(OUTPUT_PATH),
                    "download_url": f"http://localhost:{port}/files/short.mp4",
                    "size_bytes": render_result["size_bytes"],
                    "render_duration_seconds": render_result["duration_seconds"],
                    "video_provider": render_result["active_video_provider"],
                    "configured_video_provider": render_result["configured_video_provider"],
                    "provider_warnings": render_result["provider_warnings"],
                    "estimated_cost_usd": render_result.get("estimated_cost_usd", 0),
                    "publish_mode": render_result.get("publish_mode", "draft_only"),
                    "kling_preview_mode": render_result.get("kling_preview_mode", True),
                    "kling_task_ids": render_result.get("kling_task_ids", []),
                    "kling_clip_paths": render_result.get("kling_clip_paths", []),
                    "narration_used": render_result.get("narration_used", False),
                    "background_music_used": render_result.get("background_music_used", False),
                    "subtitles_burned_in": render_result.get("subtitles_burned_in", False),
                    "subtitle_path": render_result.get("subtitle_path", ""),
                    "narration_audio_path": render_result.get("narration_audio_path", ""),
                    "music_path": render_result.get("music_path", ""),
                },
            )
        except BridgeRenderError as exc:
            log_runtime_event(
                "render failed",
                stage=exc.stage,
                error=exc.error,
                details=exc.details,
            )
            self.write_json(500, exc.to_payload())
        except Exception as exc:
            error_text = str(exc) or exc.__class__.__name__
            log_runtime_event(
                "render failed",
                stage=stage,
                error=error_text,
                error_type=exc.__class__.__name__,
            )
            self.write_json(
                500,
                {
                    "ok": False,
                    "error": error_text,
                    "stage": stage,
                    "details": exc.__class__.__name__,
                },
            )

    def do_GET(self):
        parsed = urlparse(self.path)
        stage = "file_serving"
        if parsed.path not in {"/files/short.mp4", "/files/draft.mp4"}:
            self.write_json(404, {"ok": False, "error": "Not found"})
            return

        if not self.require_secret():
            self.write_json(401, {"ok": False, "error": "Missing or invalid X-ForgeView-Secret header"})
            return

        if not OUTPUT_PATH.exists():
            self.write_json(404, {"ok": False, "error": f"MP4 not found: {OUTPUT_PATH}", "stage": stage, "details": "OUTPUT_PATH does not exist"})
            return

        data = OUTPUT_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Disposition", 'attachment; filename="short.mp4"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    try:
        config = load_config()
    except Exception as exc:
        print(f"ERROR: {exc}")
        print(f"Example config: {PROJECT_ROOT / 'content' / 'config' / 'bridge_config.example.json'}")
        return 1

    ForgeViewBridgeHandler.config = config
    server = ThreadingHTTPServer((config["host"], config["port"]), ForgeViewBridgeHandler)

    print("ForgeView Local Shorts Generator Bridge")
    print("======================================")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Render endpoint: http://{config['host']}:{config['port']}/forgeview/render-short")
    print(f"MP4 endpoint: http://{config['host']}:{config['port']}/files/short.mp4")
    print("Security: requires X-ForgeView-Secret header")
    print("Do not expose this bridge publicly yet.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBridge stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
