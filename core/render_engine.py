"""Asynchronous Kling and mock video rendering for execution bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


KLING_API_BASE = os.getenv("KLING_API_BASE", "https://api-singapore.klingai.com")
KLING_CREATE_PATH = "/v1/videos/text2video"
DEFAULT_MODEL = os.getenv("KLING_MODEL", "kling-v2-6")
WORKSPACE_ROOT = Path(r"D:\ForgeViewAI")
DEFAULT_JOBS_DIR = WORKSPACE_ROOT / "output" / "media" / "jobs"


class RenderError(RuntimeError):
    """Raised when a provider request or render response is invalid."""


def ensure_workspace_path(path: Path | str) -> Path:
    resolved = Path(path).resolve()
    root = WORKSPACE_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise RenderError(f"path must stay inside {root}: {resolved}")
    return resolved


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scene_prompt(scene: dict[str, Any]) -> str:
    explicit = scene.get("prompt") or scene.get("scene_prompt")
    if explicit:
        return str(explicit).strip()

    beats = []
    for beat in scene.get("beats", []):
        screens = "; ".join(str(value) for value in beat.get("screen_content", []))
        beats.append(
            f"t+{beat.get('time', 0)}s: {beat.get('system_state', '')}. "
            f"Action: {beat.get('action', '')}. Monitors: {screens}."
        )
    return " ".join(
        value
        for value in [
            f"Vertical cinematic scene in {scene.get('location', 'an AI financial research lab')}.",
            f"Character action: {scene.get('character_action', '')}.",
            f"Camera: {scene.get('camera', '')}.",
            f"Lighting: {scene.get('lighting', '')}.",
            *beats,
            f"Glitch behavior: {scene.get('glitch', '')}.",
            f"Emotional progression: {scene.get('emotional_progression', '')}.",
            "Bloomberg terminal realism, Netflix investigative tension, legible monitors, no logos, no trading instruction.",
        ]
        if value and not value.endswith(": .")
    ).strip()


def build_kling_payload(scene: dict[str, Any]) -> dict[str, Any]:
    """Convert one execution-bundle scene into an official Kling request body."""
    prompt = _scene_prompt(scene)
    if not prompt:
        raise RenderError("scene prompt is empty")
    duration = max(5, min(10, round(float(scene.get("end", 10)) - float(scene.get("start", 0)))))
    return {
        "model_name": DEFAULT_MODEL,
        "prompt": prompt[:2500],
        "negative_prompt": (
            "unreadable text, distorted monitors, extra fingers, duplicate people, "
            "crypto coins, rockets, luxury cars, hooded hackers, logos, watermarks, "
            "trading advice, buy or sell signals"
        ),
        "mode": "pro",
        "duration": str(duration),
        "aspect_ratio": "9:16",
        "callback_url": os.getenv("KLING_CALLBACK_URL", ""),
        "external_task_id": str(scene.get("id") or ""),
    }


def _http_json(
    method: str,
    url: str,
    token: str,
    body: dict[str, Any] | None = None,
    timeout: float = 30.0,
    retries: int = 2,
) -> dict[str, Any]:
    encoded = json.dumps(body).encode("utf-8") if body is not None else None
    last_error = None
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(
                url,
                data=encoded,
                method=method,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "forgeview-content-machine/1.0",
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (
            TimeoutError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            ConnectionError,
            OSError,
        ) as error:
            last_error = error
            if attempt < retries:
                time.sleep(0.5 * (2**attempt))
    raise RenderError(f"provider request failed: {last_error!r}")


def _mock_job_id(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return f"mock_{digest}"


def _write_mock_job(job: dict[str, Any], jobs_dir: Path) -> None:
    jobs_dir = ensure_workspace_path(jobs_dir)
    jobs_dir.mkdir(parents=True, exist_ok=True)
    path = jobs_dir / f"{job['job_id']}.json"
    path.write_text(json.dumps(job, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def trigger_video_render(
    payload: dict[str, Any],
    provider: str = "mock",
    jobs_dir: Path | str = DEFAULT_JOBS_DIR,
) -> dict[str, Any]:
    """Submit a render without polling for completion."""
    if provider == "mock":
        job_id = _mock_job_id(payload)
        job = {
            "job_id": job_id,
            "provider": "kling",
            "mode": "mock",
            "status": "ready_for_upload",
            "submitted_at": utc_timestamp(),
            "payload": payload,
            "video_url": "",
            "upload_payload": {
                "scene_id": payload.get("external_task_id", ""),
                "prompt": payload["prompt"],
                "provider": "kling",
                "request": payload,
            },
        }
        _write_mock_job(job, Path(jobs_dir))
        return job

    if provider != "kling":
        raise RenderError(f"unsupported provider: {provider}")
    token = os.getenv("KLING_API_TOKEN", "").strip()
    if not token:
        raise RenderError("KLING_API_TOKEN is required for provider=kling")
    body = {key: value for key, value in payload.items() if value not in ("", None)}
    response = _http_json(
        "POST",
        f"{KLING_API_BASE}{KLING_CREATE_PATH}",
        token,
        body,
    )
    data = response.get("data") or response
    job_id = str(data.get("task_id") or data.get("job_id") or "")
    if not job_id:
        raise RenderError(f"Kling response missing task_id: {response}")
    return {
        "job_id": job_id,
        "provider": "kling",
        "mode": "api",
        "status": str(data.get("task_status") or data.get("status") or "submitted"),
        "submitted_at": utc_timestamp(),
        "payload": payload,
        "raw_response": response,
    }


def poll_render_status(
    job_id: str,
    provider: str = "mock",
    jobs_dir: Path | str = DEFAULT_JOBS_DIR,
) -> dict[str, Any]:
    """Check one render job. This function never sleeps or blocks in a loop."""
    if provider == "mock":
        path = ensure_workspace_path(Path(jobs_dir) / f"{job_id}.json")
        if not path.exists():
            raise RenderError(f"mock job not found: {job_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    if provider != "kling":
        raise RenderError(f"unsupported provider: {provider}")
    token = os.getenv("KLING_API_TOKEN", "").strip()
    if not token:
        raise RenderError("KLING_API_TOKEN is required for provider=kling")
    response = _http_json(
        "GET",
        f"{KLING_API_BASE}{KLING_CREATE_PATH}/{job_id}",
        token,
    )
    data = response.get("data") or response
    videos = data.get("task_result", {}).get("videos", []) or data.get("videos", [])
    video_url = ""
    if videos:
        video_url = str(videos[0].get("url") or videos[0].get("video_url") or "")
    return {
        "job_id": job_id,
        "provider": "kling",
        "mode": "api",
        "status": str(data.get("task_status") or data.get("status") or "unknown"),
        "video_url": video_url,
        "raw_response": response,
    }


def return_video_url(
    job_id: str,
    provider: str = "mock",
    jobs_dir: Path | str = DEFAULT_JOBS_DIR,
) -> str:
    """Return the completed video URL, or an empty string when not available."""
    status = poll_render_status(job_id, provider, jobs_dir)
    return str(status.get("video_url") or "")


def submit_execution_bundle(
    bundle: dict[str, Any],
    provider: str = "mock",
    jobs_dir: Path | str = DEFAULT_JOBS_DIR,
) -> dict[str, Any]:
    """Trigger all scene jobs and return immediately with job IDs."""
    jobs = []
    for scene in bundle.get("scenes", []):
        payload = build_kling_payload(scene)
        jobs.append(trigger_video_render(payload, provider, jobs_dir))
    updated = deepcopy(bundle)
    updated["video_render"] = {
        "status": "triggered",
        "provider": "kling",
        "mode": "api" if provider == "kling" else "mock",
        "job_ids": [job["job_id"] for job in jobs],
        "jobs": [
            {
                "scene_id": job["payload"].get("external_task_id", ""),
                "job_id": job["job_id"],
                "status": job["status"],
            }
            for job in jobs
        ],
        "final_video_url": "",
        "submitted_at": utc_timestamp(),
        "async": True,
        "text_publishing_blocked": False,
    }
    return updated


def poll_execution_bundle(
    bundle: dict[str, Any],
    provider: str | None = None,
    jobs_dir: Path | str = DEFAULT_JOBS_DIR,
) -> dict[str, Any]:
    """Poll each scene once; orchestration decides when to call again."""
    updated = deepcopy(bundle)
    render = updated.get("video_render") or {}
    mode = provider or ("kling" if render.get("mode") == "api" else "mock")
    statuses = [
        poll_render_status(job_id, mode, jobs_dir)
        for job_id in render.get("job_ids", [])
    ]
    done_statuses = {"succeed", "succeeded", "completed", "ready_for_upload"}
    failed_statuses = {"failed", "error"}
    normalized = [str(item.get("status", "")).lower() for item in statuses]
    if normalized and all(status in done_statuses for status in normalized):
        overall = "ready_for_upload" if mode == "mock" else "completed"
    elif any(status in failed_statuses for status in normalized):
        overall = "failed"
    else:
        overall = "rendering"
    urls = [str(item.get("video_url") or "") for item in statuses]
    render.update(
        {
            "status": overall,
            "jobs": statuses,
            "scene_video_urls": urls,
            "final_video_url": render.get("final_video_url", ""),
            "last_polled_at": utc_timestamp(),
        }
    )
    updated["video_render"] = render
    return updated


def _load(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save(path: Path | str, payload: dict[str, Any]) -> None:
    output = ensure_workspace_path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="ForgeView asynchronous video renderer")
    parser.add_argument("--jobs-dir", default=str(DEFAULT_JOBS_DIR))
    subparsers = parser.add_subparsers(dest="command", required=True)

    payload_parser = subparsers.add_parser("build-payloads")
    payload_parser.add_argument("--bundle", required=True)
    payload_parser.add_argument("--out", required=True)

    submit_parser = subparsers.add_parser("submit")
    submit_parser.add_argument("--bundle", required=True)
    submit_parser.add_argument("--out", required=True)
    submit_parser.add_argument("--provider", choices=("mock", "kling"), default="mock")

    poll_parser = subparsers.add_parser("poll")
    poll_parser.add_argument("--bundle", required=True)
    poll_parser.add_argument("--out", required=True)
    poll_parser.add_argument("--provider", choices=("mock", "kling"))

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--job-id", required=True)
    status_parser.add_argument("--provider", choices=("mock", "kling"), default="mock")

    args = parser.parse_args()
    jobs_dir = ensure_workspace_path(args.jobs_dir)
    if args.command == "build-payloads":
        bundle = _load(args.bundle)
        _save(args.out, {"requests": [build_kling_payload(scene) for scene in bundle.get("scenes", [])]})
    elif args.command == "submit":
        _save(
            args.out,
            submit_execution_bundle(_load(args.bundle), args.provider, jobs_dir),
        )
    elif args.command == "poll":
        _save(
            args.out,
            poll_execution_bundle(_load(args.bundle), args.provider, jobs_dir),
        )
    elif args.command == "status":
        print(json.dumps(poll_render_status(args.job_id, args.provider, jobs_dir), indent=2))


if __name__ == "__main__":
    main()
