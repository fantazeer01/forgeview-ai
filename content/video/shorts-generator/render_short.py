import argparse
import base64
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
import wave
import struct
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


WIDTH = 1080
HEIGHT = 1920
FPS = 30
SCENE_SECONDS = 3.8
TRANSITION_SECONDS = 0.4
SCENE_KEYS = [f"scene{i}" for i in range(1, 8)]
STORY_ROLES = [
    "shocking hook",
    "hidden danger",
    "what breaks",
    "why normal logic fails",
    "fix discovered",
    "proof/test",
    "final principle",
]
SCENE_VISUALS = [
    "anonymous founder in a black hoodie standing beside a serious autonomous trading-risk core in a charcoal automation room, yellow warning accent light, black metal hardware, exposed cables, high-stakes system failure, no toy robot",
    "same anonymous hoodie founder facing a locked mechanical gate inside the same charcoal automation room, yellow edge light reveals a trapped bot module, cooldown trap metaphor, no signs",
    "same founder seen from behind near a glowing escape corridor blocked by a heavy mechanical barrier, small trading bot silhouette trapped behind a closing gate, yellow risk light, exit path visibly blocked",
    "same founder studying two physical decision paths crossing incorrectly through a broken automation circuit, wrong branch marked only by yellow light, snapped logic conduit, no panels",
    "same founder reconnecting a safety circuit inside a risk manager module, yellow safe path opening, entry path blocked while exit path remains open, no EXIT sign, no labels",
    "same founder in a dark testing lab inspecting the trading bot module with probes, yellow verification light, black/charcoal equipment, no screens or panels with characters",
    "same founder looking at a stable ForgeView automation control room, protected exit corridor open, entry gate controlled, calm black and charcoal environment with yellow accents, no sci-fi fantasy",
]
BG = (10, 14, 22)
FG = (245, 247, 250)
MUTED = (142, 152, 166)
ACCENT = (246, 190, 60)
PROMPT_STYLE = "ForgeView visual system: black charcoal backgrounds, white overlays, yellow accent lighting, recurring anonymous hoodie founder, cinematic automation story"
NO_TEXT_IMAGE_RULE = "no text, no letters, no words, no captions, no logos, no signs, no labels, no UI screens, no fake letters, no fake words, no readable symbols, no readable marks"
OPENAI_CONFIG_PATH = Path(r"D:\ForgeViewAI\content\config\openai_config.json")
OPENAI_IMAGE_MODEL = "gpt-image-1"
OPENAI_IMAGE_SIZE = "1024x1536"
OPENAI_IMAGE_QUALITY = "low"
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"
OPENAI_TTS_VOICE = "alloy"
DEFAULT_MUSIC_PATH = Path(r"D:\ForgeViewAI\output\media\videos\background.mp3")


def parse_args():
    parser = argparse.ArgumentParser(description="Render a ForgeView Shorts JSON draft to vertical MP4.")
    parser.add_argument("--input", default="example_short.json", help="Path to Shorts draft JSON.")
    parser.add_argument("--output", default="output/short.mp4", help="Output MP4 path.")
    parser.add_argument("--workdir", default="work", help="Temporary slide directory.")
    parser.add_argument("--prompts", default="scene_prompts.json", help="Output path for scene image prompts.")
    parser.add_argument("--music", default=str(DEFAULT_MUSIC_PATH), help="Optional MP3 background music path.")
    parser.add_argument("--voice-script", default="voice_script.txt", help="Output path for narration script.")
    parser.add_argument("--subtitles", default="subtitles.srt", help="Output path for generated subtitles.")
    parser.add_argument("--seconds", type=float, default=SCENE_SECONDS, help="Seconds per scene.")
    return parser.parse_args()


def load_font(size):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def text_height(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[3] - box[1]


def wrap_text(draw, text, font, max_width):
    words = str(text).strip().split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        test = f"{current} {word}"
        if text_width(draw, test, font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit_font(draw, text, max_width, max_height, start_size=92, min_size=44):
    for size in range(start_size, min_size - 1, -2):
        font = load_font(size)
        lines = wrap_text(draw, text, font, max_width)
        line_gap = int(size * 0.28)
        total_height = sum(text_height(draw, line, font) for line in lines) + line_gap * (len(lines) - 1)
        if total_height <= max_height and all(text_width(draw, line, font) <= max_width for line in lines):
            return font, lines, line_gap
    font = load_font(min_size)
    return font, wrap_text(draw, text, font, max_width), int(min_size * 0.28)


def scene_seed(text):
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def clamp(value):
    return max(0, min(255, int(value)))


def blend(a, b, t):
    return tuple(clamp(a[i] * (1 - t) + b[i] * t) for i in range(3))


def clean_caption(text, max_words=6):
    words = str(text).strip().split()
    return " ".join(words[:max_words])


def caption_lines(draw, text, font, max_width):
    words = clean_caption(text).split()
    if not words:
        return [""]

    if text_width(draw, " ".join(words), font) <= max_width:
        return [" ".join(words)]

    best_lines = None
    best_score = None
    for split_at in range(1, len(words)):
        lines = [" ".join(words[:split_at]), " ".join(words[split_at:])]
        if any(text_width(draw, line, font) > max_width for line in lines):
            continue
        score = abs(len(lines[0]) - len(lines[1]))
        if best_score is None or score < best_score:
            best_lines = lines
            best_score = score

    if best_lines:
        return best_lines

    return wrap_text(draw, " ".join(words), font, max_width)[:2]


def fit_caption_font(draw, text, max_width, max_height, start_size=98, min_size=62):
    for size in range(start_size, min_size - 1, -2):
        font = load_font(size)
        lines = caption_lines(draw, text, font, max_width)
        line_gap = int(size * 0.20)
        total_height = sum(text_height(draw, line, font) for line in lines) + line_gap * (len(lines) - 1)
        if len(lines) <= 2 and total_height <= max_height:
            return font, lines, line_gap
    font = load_font(min_size)
    return font, caption_lines(draw, text, font, max_width), int(min_size * 0.20)


def draw_shadowed_text(draw, position, text, font, fill):
    x, y = position
    for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 3)]:
        draw.text((x + dx, y + dy), text, fill=(0, 0, 0), font=font)
    draw.text((x, y), text, fill=fill, font=font)


def draw_text_box(frame, text, box, start_size=98, min_size=62, fill=(0, 0, 0, 232)):
    left, top, right, bottom = box
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle((left, top, right, bottom), radius=34, fill=fill)
    frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(frame)

    max_width = right - left - 120
    max_height = bottom - top - 72
    font, lines, line_gap = fit_caption_font(draw, text, max_width, max_height, start_size=start_size, min_size=min_size)
    total_height = sum(text_height(draw, line, font) for line in lines) + line_gap * (len(lines) - 1)
    y = top + ((bottom - top - total_height) // 2)
    for line in lines[:2]:
        w = text_width(draw, line, font)
        draw_shadowed_text(draw, ((WIDTH - w) // 2, y), line, font, (255, 255, 255))
        y += text_height(draw, line, font) + line_gap

    return frame


def draw_hook_caption(frame, text):
    box = (
        int(WIDTH * 0.055),
        int(HEIGHT * 0.39),
        int(WIDTH * 0.945),
        int(HEIGHT * 0.56),
    )
    return draw_text_box(frame, text, box, start_size=104, min_size=66, fill=(0, 0, 0, 220))


def build_narration_line(scene_text, index):
    templates = [
        "This bug could trap every trade.",
        "The bot thinks the cooldown is protecting it.",
        "But the exit can get blocked too.",
        "That is where normal risk logic fails.",
        "We changed the risk manager.",
        "Now exits stay open during cooldown.",
        "Never block recovery.",
    ]
    if index <= len(templates):
        return templates[index - 1]
    return clean_caption(scene_text) + "."


def build_voice_script(scenes):
    return [build_narration_line(scene, index) for index, scene in enumerate(scenes, start=1)]


def format_srt_time(seconds):
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def write_voice_script(path, narration_lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(narration_lines) + "\n", encoding="utf-8")


def write_subtitles(path, narration_lines, seconds):
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = []
    for index, line in enumerate(narration_lines, start=1):
        start = (index - 1) * seconds
        end = index * seconds - 0.15
        blocks.append(
            f"{index}\n"
            f"{format_srt_time(start)} --> {format_srt_time(end)}\n"
            f"{line}\n"
        )
    path.write_text("\n".join(blocks), encoding="utf-8")


def generate_tts(path, narration_text, api_key):
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


def subtitle_for_frame(narration_lines, scene_index):
    if 0 <= scene_index < len(narration_lines):
        return narration_lines[scene_index]
    return ""


def draw_subtitle(frame, subtitle_text):
    if not subtitle_text:
        return frame

    left = int(WIDTH * 0.06)
    right = int(WIDTH * 0.94)
    top = int(HEIGHT * 0.875)
    bottom = int(HEIGHT * 0.975)
    frame = draw_text_box(frame, subtitle_text, (left, top, right, bottom), start_size=38, min_size=26, fill=(0, 0, 0, 190))
    return frame


def generate_scene_prompt(title, description, scene_text, index, previous_scene_text="", previous_visual=""):
    clean_description = " ".join(str(description).split())[:180]
    role = STORY_ROLES[index - 1] if index <= len(STORY_ROLES) else "scene"
    visual = SCENE_VISUALS[index - 1] if index <= len(SCENE_VISUALS) else "distinct cinematic automation visual"
    if previous_scene_text or previous_visual:
        previous_context = (
            f"previous scene continuity: previous story moment was '{previous_scene_text}', "
            f"previous visual used '{previous_visual}', keep the same anonymous hoodie founder, same ForgeView room, same black/charcoal/yellow visual language, "
        )
    else:
        previous_context = (
            "opening scene continuity: introduce the anonymous hoodie founder and the ForgeView black/charcoal/yellow visual language, "
        )
    return "".join([
        "cinematic close-up, ultra cinematic, film still, high production value, depth of field, "
        "dramatic composition, professional lighting, realistic movie-like scene, strong foreground subject, clear emotion, "
        "environmental storytelling, vertical 9:16 visual background only, zero readable text anywhere, "
        "single coherent visual system across all scenes: dark black and charcoal background, white caption-safe negative space, yellow ForgeView accent lighting, "
        "recurring protagonist: anonymous founder in a plain black hoodie, face partially hidden or turned away, same person appears across scenes, "
        f"scene {index}, story role: {role}, visual: {visual}, ",
        previous_context,
        f"topic: {scene_text}, title: {title}, context: {clean_description}, "
        "dark ForgeView tech style, AI automation, trading bot, and risk system feeling, no typography, no signage, "
        "ForgeViewAI build-in-public automation and trading project identity, "
        "visual metaphors for Telegram trading bot alerts, BTC/USDT paper trades, "
        "workflow automation, Risk Manager logic, cooldown block gates, protected exits, filtered entries, without fake UI, "
        "v22 Exit Safety and v23 RSI Anti Late Short represented as physical reliability checks, "
        "interfaces must be implied through cinematic objects, paths, lights, gates, agent modules, and warning glows without screenshots, dashboards, or readable UI, "
        "if a screen-like object appears it must be blank or abstract light only, no characters, no letters, no numbers, no words, "
        "high contrast composition, main subject in upper and middle frame, bottom safe area clear for subtitles, "
        "avoid fantasy objects, avoid random clocks, avoid abstract boxes, avoid medieval or steampunk visuals, "
        "avoid unrelated control rooms, avoid people staring at monitors, avoid generic dashboards, avoid UI screenshots, "
        "avoid Telegram screens, avoid n8n screens, avoid terminal windows, avoid chart labels, avoid code editors, avoid UI screens, avoid fake letters, avoid EXIT signs, avoid warning signs with text, "
        "avoid stock-photo offices, avoid generic business imagery, no fake metrics, no hype, "
        f"strict image rule: {NO_TEXT_IMAGE_RULE}, no watermarks"
    ])


def build_scene_prompts(title, description, scenes):
    items = []
    for index, scene_text in enumerate(scenes, start=1):
        previous_scene_text = scenes[index - 2] if index > 1 and index - 2 < len(scenes) else ""
        previous_visual = SCENE_VISUALS[index - 2] if index > 1 and index - 2 < len(SCENE_VISUALS) else ""
        items.append(
            {
                "scene": f"scene{index}",
                "story_role": STORY_ROLES[index - 1] if index <= len(STORY_ROLES) else "scene",
                "visual_concept": SCENE_VISUALS[index - 1] if index <= len(SCENE_VISUALS) else "distinct cinematic automation visual",
                "previous_scene_context": previous_scene_text,
                "previous_visual_context": previous_visual,
                "image": f"image{index}",
                "caption": clean_caption(scene_text),
                "prompt": generate_scene_prompt(title, description, scene_text, index, previous_scene_text, previous_visual),
            }
        )
    return {
        "style": PROMPT_STYLE,
        "image_model": OPENAI_IMAGE_MODEL,
        "image_size": OPENAI_IMAGE_SIZE,
        "image_quality": OPENAI_IMAGE_QUALITY,
        "mapping": items,
    }


def load_openai_api_key(config_path):
    if not config_path.exists():
        print("OpenAI config missing, using placeholder images")
        return None

    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"OpenAI config invalid, using placeholder images: {exc}")
        return None

    api_key = str(config.get("api_key", "")).strip()
    if not api_key or api_key == "PUT_API_KEY_HERE":
        print("OpenAI config incomplete, using placeholder images")
        return None

    return api_key


def normalize_image(path):
    with Image.open(path) as source:
        image = source.convert("RGB")
        image = ImageOps.fit(image, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        image.save(path, "PNG")


def generate_openai_image(path, prompt, api_key):
    payload = {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": prompt,
        "size": OPENAI_IMAGE_SIZE,
        "quality": OPENAI_IMAGE_QUALITY,
        "output_format": "png",
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    image_base64 = result["data"][0]["b64_json"]
    path.write_bytes(base64.b64decode(image_base64))
    normalize_image(path)
    return result.get("usage")


def generate_openai_image_with_retries(path, prompt, api_key, attempts=3):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return generate_openai_image(path, prompt, api_key)
        except (OSError, urllib.error.URLError, TimeoutError, ConnectionError, KeyError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < attempts:
                print(f"OpenAI image retry {attempt + 1}/{attempts} after error: {exc}")
                time.sleep(4 * attempt)
    raise last_error


def draw_cinematic_image(path, prompt, scene_text, index):
    seed = scene_seed(f"{prompt}|{scene_text}|{index}")
    palette = [
        ((8, 12, 22), (28, 92, 128), (76, 195, 255)),
        ((10, 14, 22), (62, 48, 120), (92, 220, 190)),
        ((9, 16, 24), (104, 70, 32), (255, 190, 88)),
        ((7, 12, 18), (38, 88, 68), (97, 231, 134)),
    ][seed % 4]

    image = Image.new("RGB", (WIDTH, HEIGHT), palette[0])
    pixels = image.load()
    for y in range(HEIGHT):
        vertical = y / HEIGHT
        for x in range(WIDTH):
            diagonal = (x / WIDTH) * 0.38
            wave = (math.sin((x + seed % 500) / 92) + math.cos((y + seed % 700) / 134)) * 0.035
            color = blend(palette[0], palette[1], min(1, vertical * 0.85 + diagonal + wave))
            pixels[x, y] = color

    draw = ImageDraw.Draw(image)

    for i in range(8):
        offset = (seed >> (i * 3)) % 360
        x1 = 80 + (offset * 7) % 780
        y1 = 280 + (offset * 11) % 1080
        x2 = x1 + 220 + (offset % 180)
        y2 = y1 + 120 + (offset % 260)
        outline = blend(palette[2], (255, 255, 255), 0.12)
        draw.rounded_rectangle((x1, y1, x2, y2), radius=28, outline=outline, width=2)

    for i in range(9):
        x = 120 + i * 110
        height = 80 + ((seed >> i) % 280)
        draw.rounded_rectangle(
            (x, HEIGHT - 390 - height, x + 46, HEIGHT - 390),
            radius=16,
            fill=blend(palette[2], palette[0], 0.45),
        )

    for i in range(14):
        x = 70 + i * 76
        y = 360 + int(math.sin(i + seed % 19) * 80)
        draw.ellipse((x, y, x + 10, y + 10), fill=palette[2])
        if i:
            prev_x = 70 + (i - 1) * 76 + 5
            prev_y = 360 + int(math.sin(i - 1 + seed % 19) * 80) + 5
            draw.line((prev_x, prev_y, x + 5, y + 5), fill=blend(palette[2], FG, 0.25), width=4)

    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0, 76))
    draw.rectangle((0, 0, WIDTH, 14), fill=palette[2])
    image.save(path, "PNG")


def draw_slide(path, backplate_path, title, scene_text, index, total):
    image = Image.open(backplate_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    brand_font = load_font(34)
    small_font = load_font(30)

    draw.text((84, 78), "ForgeViewAI", fill=ACCENT, font=brand_font)
    draw.text((WIDTH - 170, 80), f"{index}/{total}", fill=MUTED, font=small_font)

    image.save(path, "PNG")


def animated_scene_frame(source, scene_index, frame_index, frame_count):
    progress = frame_index / max(1, frame_count - 1)
    seed = scene_seed(f"motion|{scene_index}")
    zoom_in = seed % 2 == 0
    pan_right = seed % 3 != 0
    zoom_progress = progress if zoom_in else 1 - progress
    eased = progress * progress * (3 - 2 * progress)
    if scene_index == 1:
        zoom = 1.055 + 0.095 * eased
    else:
        zoom = 1.035 + 0.065 * zoom_progress

    scaled_width = int(WIDTH * zoom)
    scaled_height = int(HEIGHT * zoom)
    resized = source.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    max_x = scaled_width - WIDTH
    max_y = scaled_height - HEIGHT
    x_progress = progress if pan_right else 1 - progress
    y_wave = 0.5 + math.sin((progress * math.pi * 2) + (seed % 17)) * 0.16
    x = int(max_x * x_progress)
    y = int(max_y * max(0, min(1, y_wave)))

    return resized.crop((x, y, x + WIDTH, y + HEIGHT))


def generate_motion_frames(slide_paths, frame_dir, seconds, transition_seconds, narration_lines, hook_text):
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)

    scene_frames = int(seconds * FPS)
    transition_frames = max(1, int(transition_seconds * FPS))
    slides = [Image.open(path).convert("RGB") for path in slide_paths]
    frame_number = 1

    for scene_index, slide in enumerate(slides):
        next_slide = slides[scene_index + 1] if scene_index + 1 < len(slides) else None
        for frame_index in range(scene_frames):
            frame = animated_scene_frame(slide, scene_index + 1, frame_index, scene_frames)

            if next_slide and frame_index >= scene_frames - transition_frames:
                fade_index = frame_index - (scene_frames - transition_frames) + 1
                alpha = fade_index / transition_frames
                next_frame = animated_scene_frame(next_slide, scene_index + 2, fade_index, scene_frames)
                frame = Image.blend(frame, next_frame, alpha)

            if scene_index == 0 and frame_index < int(2 * FPS):
                frame = draw_hook_caption(frame, hook_text)
            frame = draw_subtitle(frame, subtitle_for_frame(narration_lines, scene_index))
            frame.save(frame_dir / f"frame_{frame_number:05d}.png", "PNG")
            frame_number += 1

    for slide in slides:
        slide.close()

    return frame_number - 1


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
        for sample_index in range(total_samples):
            t = sample_index / sample_rate
            beat_pos = t % beat_interval
            kick = math.exp(-beat_pos * 15) * math.sin(2 * math.pi * 54 * t)
            sub = 0.42 * math.sin(2 * math.pi * 44 * t)
            pulse = 0.38 * math.sin(2 * math.pi * 88 * t)
            texture = 0.14 * math.sin(2 * math.pi * 176 * t + math.sin(t * 2.0))
            sidechain = 0.48 + 0.52 * min(1.0, beat_pos / max(0.001, beat_interval * 0.45))
            value = (kick * 0.85 + sub * sidechain + pulse * sidechain + texture) * 0.38
            value = max(-1.0, min(1.0, value))
            wav.writeframes(struct.pack("<h", int(value * 32767)))


def media_duration(path, stream_selector=None):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe or not path or not Path(path).exists():
        return 0.0

    cmd = [
        ffprobe,
        "-v",
        "error",
    ]
    if stream_selector:
        cmd.extend(["-select_streams", stream_selector])
        cmd.extend(["-show_entries", "stream=duration"])
    else:
        cmd.extend(["-show_entries", "format=duration"])
    cmd.extend(["-of", "default=noprint_wrappers=1:nokey=1", str(path)])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0
    for line in result.stdout.splitlines():
        try:
            value = float(line.strip())
            if value > 0:
                return value
        except ValueError:
            continue
    return 0.0


def audio_stream_count(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe or not path or not Path(path).exists():
        return 0

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0
    return len([line for line in result.stdout.splitlines() if line.strip()])


def run_ffmpeg(frame_dir, output, duration, music_path, narration_path):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg not found in PATH. Install FFmpeg and restart the terminal.")

    pattern = str(Path(frame_dir) / "frame_%05d.png")
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        pattern,
    ]

    narration_exists = narration_path and Path(narration_path).exists()
    music_exists = music_path and Path(music_path).exists()

    if narration_exists:
        cmd.extend(["-i", str(narration_path)])

    if music_exists:
        cmd.extend(["-stream_loop", "-1", "-i", str(music_path)])

    cmd.extend(
        [
            "-t",
            f"{duration:.3f}",
            "-r",
            str(FPS),
        ]
    )

    if narration_exists and music_exists:
        cmd.extend([
            "-filter_complex",
            f"[1:a]volume=1.0,apad,atrim=0:{duration:.3f}[a0];"
            f"[2:a]volume=0.30,atrim=0:{duration:.3f}[a1];"
            f"[a0][a1]amix=inputs=2:duration=longest:normalize=0:dropout_transition=0,"
            f"atrim=0:{duration:.3f}[aout]",
            "-map",
            "0:v",
            "-map",
            "[aout]",
        ])
    elif narration_exists:
        cmd.extend([
            "-filter_complex",
            f"[1:a]volume=1.0,apad,atrim=0:{duration:.3f}[aout]",
            "-map",
            "0:v",
            "-map",
            "[aout]",
        ])
    elif music_exists:
        cmd.extend([
            "-filter_complex",
            f"[1:a]volume=0.30,atrim=0:{duration:.3f}[aout]",
            "-map",
            "0:v",
            "-map",
            "[aout]",
        ])

    cmd.extend([
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "scale=1080:1920",
        "-movflags",
        "+faststart",
    ])

    if narration_exists or music_exists:
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])

    cmd.append(str(output))
    subprocess.run(cmd, check=True)


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    workdir = Path(args.workdir)
    prompts_path = Path(args.prompts)
    image_dir = workdir / "images"
    frame_dir = workdir / "frames"
    audio_dir = workdir / "audio"
    narration_path = audio_dir / "narration.mp3"
    music_path = Path(args.music) if args.music else None
    voice_script_path = Path(args.voice_script)
    subtitles_path = Path(args.subtitles)

    if args.seconds <= 0:
        raise ValueError("--seconds must be positive.")

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "ForgeView Short")
    description = data.get("description", "")
    scenes = [str(data.get(key, "")).strip() for key in SCENE_KEYS]
    scenes = [scene for scene in scenes if scene]

    if not scenes:
        raise ValueError("Input JSON must include at least one non-empty scene field.")

    duration = len(scenes) * args.seconds
    if duration < 25 or duration > 45:
        print(
            f"Warning: duration will be {duration:.1f}s. "
            "Recommended Shorts MVP duration is 25-45s.",
            file=sys.stderr,
        )

    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompts_path.parent.mkdir(parents=True, exist_ok=True)

    narration_lines = build_voice_script(scenes)
    write_voice_script(voice_script_path, narration_lines)
    write_subtitles(subtitles_path, narration_lines, args.seconds)

    scene_prompts = build_scene_prompts(title, description, scenes)
    scene_prompts["voice_over"] = {
        "model": OPENAI_TTS_MODEL,
        "voice": OPENAI_TTS_VOICE,
        "voice_script_path": str(voice_script_path),
        "narration_audio_path": str(narration_path),
        "subtitles_path": str(subtitles_path),
        "lines": narration_lines,
    }
    with prompts_path.open("w", encoding="utf-8") as f:
        json.dump(scene_prompts, f, ensure_ascii=False, indent=2)

    openai_api_key = load_openai_api_key(OPENAI_CONFIG_PATH)

    if openai_api_key:
        print("Generating OpenAI voice-over...")
        generate_tts(narration_path, " ".join(narration_lines), openai_api_key)
    else:
        print("OpenAI config missing, rendered without voice-over")

    if not (music_path and music_path.exists()):
        builtin_music_path = audio_dir / "builtin_dark_tech_beat.wav"
        print("Background music file missing, generating built-in dark tech beat...")
        generate_builtin_music(builtin_music_path, duration)
        music_path = builtin_music_path

    slide_paths = []

    for i, scene in enumerate(scenes, start=1):
        prompt = scene_prompts["mapping"][i - 1]["prompt"]
        image_path = image_dir / f"image{i}.png"
        slide_path = workdir / f"scene_{i:02d}.png"
        source = "placeholder"
        error = None
        usage = None

        if openai_api_key:
            try:
                print(f"Generating OpenAI image {i}/{len(scenes)}...")
                usage = generate_openai_image_with_retries(image_path, prompt, openai_api_key)
                source = "openai"
            except (OSError, urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
                error = str(exc)
                print(f"OpenAI image generation failed for image{i}, using placeholder: {error}")
                draw_cinematic_image(image_path, prompt, scene, i)
        else:
            draw_cinematic_image(image_path, prompt, scene, i)

        scene_prompts["mapping"][i - 1]["image_file"] = str(image_path)
        scene_prompts["mapping"][i - 1]["image_source"] = source
        scene_prompts["mapping"][i - 1]["generation"] = {
            "model": OPENAI_IMAGE_MODEL,
            "requested_size": OPENAI_IMAGE_SIZE,
            "normalized_size": f"{WIDTH}x{HEIGHT}",
            "quality": OPENAI_IMAGE_QUALITY,
            "usage": usage,
            "fallback_error": error,
        }
        draw_slide(slide_path, image_path, title, scene, i, len(scenes))
        slide_paths.append(slide_path)

    scene_prompts["effects"] = {
        "ken_burns": True,
        "pan": True,
        "crossfade_seconds": TRANSITION_SECONDS,
        "fps": FPS,
        "background_music_path": str(music_path) if music_path else None,
        "background_music_used": bool(music_path and music_path.exists()),
        "background_music_volume": 0.30,
        "narration_used": narration_path.exists(),
        "narration_volume": 1.0,
        "subtitles_burned_in": True,
        "subtitle_safe_area": "bottom 12%",
    }

    with prompts_path.open("w", encoding="utf-8") as f:
        json.dump(scene_prompts, f, ensure_ascii=False, indent=2)

    frame_count = generate_motion_frames(
        slide_paths,
        frame_dir,
        args.seconds,
        TRANSITION_SECONDS,
        narration_lines,
        scenes[0],
    )
    run_ffmpeg(frame_dir, output_path, duration, music_path, narration_path)
    final_video_duration = media_duration(output_path)
    narration_duration = media_duration(narration_path)
    music_duration = media_duration(music_path)
    final_audio_duration = media_duration(output_path, "a:0")
    final_audio_streams = audio_stream_count(output_path)
    print(f"Rendered MP4: {output_path.resolve()}")
    print(f"Scene prompts: {prompts_path.resolve()}")
    print(f"Voice script: {voice_script_path.resolve()}")
    print(f"Subtitles: {subtitles_path.resolve()}")
    print(f"Resolution: {WIDTH}x{HEIGHT}")
    print(f"Duration: {duration:.1f}s")
    print(f"Validation video duration: {final_video_duration:.2f}s")
    print(f"Validation narration.mp3 duration: {narration_duration:.2f}s")
    print(f"Validation music duration: {music_duration:.2f}s")
    print(f"Validation final MP4 audio duration: {final_audio_duration:.2f}s")
    print(f"Validation final MP4 audio streams: {final_audio_streams}")
    print(f"Validation voice included: {'yes' if narration_path.exists() and final_audio_streams >= 1 else 'no'}")
    print(f"Validation music mixed: {'yes' if music_path and music_path.exists() and final_audio_duration >= duration - 0.5 else 'no'}")
    print(f"Motion frames: {frame_count}")
    if narration_path.exists():
        print(f"Narration audio: {narration_path.resolve()}")
    if music_path and music_path.exists():
        print(f"Background music: {music_path.resolve()}")
    else:
        print("Background music: not found, rendered without audio")


if __name__ == "__main__":
    main()
