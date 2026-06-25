# ForgeView Shorts Generator v2

## Goal

Convert a ForgeView Shorts Draft JSON into a ready-to-upload vertical MP4.

This MVP is local, Windows-compatible, and Creatomate-free.

It renders cinematic image-backed scenes with large centered captions. It creates
`scene_prompts.json`, generates scene images with OpenAI when configured, and falls back
to local placeholder backplates when image generation is unavailable.

## Input Format

```json
{
  "title": "...",
  "description": "...",
  "scene1": "...",
  "scene2": "...",
  "scene3": "...",
  "scene4": "...",
  "scene5": "...",
  "scene6": "...",
  "scene7": "..."
}
```

## Output

Default output:

```text
output/short.mp4
```

Video settings:

- Resolution: `1080x1920`
- Format: vertical MP4
- Duration: 7 scenes x 4 seconds = 28 seconds
- Captions: one large centered caption per scene
- Background: generated cinematic ForgeView-style image backplate per scene

Prompt output:

```text
scene_prompts.json
```

Image mapping:

```text
scene1 -> image1
scene2 -> image2
scene3 -> image3
scene4 -> image4
scene5 -> image5
scene6 -> image6
scene7 -> image7
```

## Requirements

- Python 3.10+
- FFmpeg installed and available in `PATH`
- Python package: `Pillow`

## Easiest Use: Double-Click Launcher

For non-technical use, double-click:

```text
RUN_SHORTS.bat
```

It will automatically:

1. Check Python.
2. Check FFmpeg.
3. Install Python requirements if needed.
4. Generate `scene_prompts.json`.
5. Generate one OpenAI image per scene if `D:\ForgeViewAI\content\config\openai_config.json` exists.
6. Fall back to local placeholder backplates if image generation fails.
7. Render `example_short.json`.
8. Save the MP4.
9. Send the MP4 to Telegram if `D:\ForgeViewAI\content\config\telegram_config.json` exists.
10. Pause at the end so you can see success or errors.

Output video:

```text
D:\ForgeViewAI\output\media\videos\short.mp4
```

## Clipboard Mode

If you copied a Shorts draft JSON from Telegram, n8n, or ChatGPT, double-click:

```text
RUN_SHORTS_FROM_CLIPBOARD.bat
```

It will:

1. Read the JSON currently copied to your clipboard.
2. Save it as `clipboard_short.json`.
3. Generate scene prompts and image backplates.
4. Render it to `output/short.mp4`.
4. Pause at the end.

Make sure your clipboard contains the full JSON object, including:

```json
{
  "title": "...",
  "description": "...",
  "scene1": "...",
  "scene2": "...",
  "scene3": "...",
  "scene4": "...",
  "scene5": "...",
  "scene6": "...",
  "scene7": "..."
}
```

## Install Python Dependencies

From this folder:

```powershell
pip install -r requirements.txt
```

If `pip` is not recognized, try:

```powershell
python -m pip install -r requirements.txt
```

## FFmpeg Setup On Windows

Option A: Install with winget:

```powershell
winget install Gyan.FFmpeg
```

Option B: Manual install:

1. Download FFmpeg from:
   ```text
   https://www.gyan.dev/ffmpeg/builds/
   ```
2. Extract the archive.
3. Add the `bin` folder to Windows `PATH`.
4. Restart PowerShell.
5. Verify:
   ```powershell
   ffmpeg -version
   ```

## Render Example Video

From this folder:

```powershell
python render_short.py --input example_short.json --output output/short.mp4
```

Expected output path:

```text
D:\ForgeViewAI\output\media\videos\short.mp4
```

## Render A Custom Draft

```powershell
python render_short.py --input path\to\your_short.json --output output\my_short.mp4
```

## Duration Control

Default scene duration is 4 seconds.

```powershell
python render_short.py --seconds 5
```

With 7 scenes:

- 4 seconds per scene = 28 seconds
- 5 seconds per scene = 35 seconds
- 6 seconds per scene = 42 seconds

Keep the final video between 25 and 45 seconds.

## OpenAI Image Generation

Create this local config file:

```text
D:\ForgeViewAI\content\config\openai_config.json
```

Format:

```json
{
  "api_key": "PUT_API_KEY_HERE"
}
```

The example file is:

```text
D:\ForgeViewAI\content\config\openai_config.example.json
```

The renderer uses:

```text
model: gpt-image-1
size: 1024x1536
quality: low
output: PNG normalized to 1080x1920
```

Generated scene images are saved here:

```text
D:\ForgeViewAI\content\video\shorts-generator\work\images
```

## Notes

- No manual editing is required.
- AI image generation is optional.
- The script creates local cinematic image backplates in `work/images/`.
- The script creates temporary slide PNG files in `work/`.
- The script creates `scene_prompts.json` with prompts, image paths, generation source, and fallback errors.
- FFmpeg combines the slides into the final MP4.
- YouTube upload is still manual for the MVP.

## Files

```text
README.md
requirements.txt
example_short.json
render_short.py
send_telegram_video.py
RUN_SHORTS.bat
RUN_SHORTS_FROM_CLIPBOARD.bat
scene_prompts.json
output/
work/
```
