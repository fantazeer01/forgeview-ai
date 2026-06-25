from __future__ import annotations

import math
from datetime import datetime
from typing import Iterable


FATAL_CAPTURE_EVENTS = {
    "capture_fatal_error",
    "fatal_capture_error",
    "fatal_error",
}


def observation_continuity(
    *,
    expected_duration_seconds: float,
    poll_interval_seconds: float,
    started_at: datetime,
    completed_at: datetime | None,
    checkpoint_timestamps: Iterable[datetime],
    fatal_capture_errors: int = 0,
) -> dict:
    checkpoints = sorted(set(checkpoint_timestamps))
    expected_count = max(
        1, math.ceil(expected_duration_seconds / poll_interval_seconds)
    )
    actual_count = len(checkpoints)
    checkpoint_coverage = min(1.0, actual_count / expected_count)
    session_completed = completed_at is not None
    observed_utc_span = (
        max(0.0, (completed_at - started_at).total_seconds())
        if completed_at else 0.0
    )
    temporal_coverage = min(
        1.0,
        observed_utc_span / expected_duration_seconds
        if expected_duration_seconds else 0.0,
    )

    boundaries = [started_at, *checkpoints]
    if completed_at is not None:
        boundaries.append(completed_at)
    gaps = [
        max(0.0, (right - left).total_seconds())
        for left, right in zip(boundaries, boundaries[1:])
    ]
    max_gap = max(gaps, default=0.0)
    terminal_gap = (
        max(0.0, (completed_at - checkpoints[-1]).total_seconds())
        if completed_at is not None and checkpoints else observed_utc_span
    )
    effective_duration = (
        max(0.0, (checkpoints[-1] - checkpoints[0]).total_seconds())
        if len(checkpoints) >= 2 else 0.0
    )

    rejection_reasons: list[str] = []
    if temporal_coverage < 0.99:
        rejection_reasons.append("temporal_coverage_below_99_percent")
    if checkpoint_coverage < 0.95:
        rejection_reasons.append("checkpoint_coverage_below_95_percent")
    if max_gap > 300.0:
        rejection_reasons.append("checkpoint_gap_over_300_seconds")
    if not session_completed:
        rejection_reasons.append("session_completed_missing")
    if fatal_capture_errors:
        rejection_reasons.append("fatal_capture_errors_present")

    return {
        "status": "continuous" if not rejection_reasons else "incomplete",
        "expected_checkpoint_count": expected_count,
        "actual_checkpoint_count": actual_count,
        "checkpoint_coverage_percentage": round(
            checkpoint_coverage * 100.0, 4
        ),
        "max_checkpoint_gap_seconds": round(max_gap, 6),
        "gaps_over_10_seconds": sum(gap > 10.0 for gap in gaps),
        "gaps_over_60_seconds": sum(gap > 60.0 for gap in gaps),
        "gaps_over_300_seconds": sum(gap > 300.0 for gap in gaps),
        "effective_observed_duration_seconds": round(effective_duration, 6),
        "first_observation_timestamp": (
            checkpoints[0].isoformat() if checkpoints else None
        ),
        "last_observation_timestamp": (
            checkpoints[-1].isoformat() if checkpoints else None
        ),
        "terminal_gap_seconds": round(terminal_gap, 6),
        "session_completed_present": session_completed,
        "fatal_capture_error_count": fatal_capture_errors,
        "rejection_reasons": rejection_reasons,
    }


def session_continuity(events: list[dict]) -> dict:
    started = next(
        (event for event in events if event.get("event") == "session_started"),
        None,
    )
    if started is None:
        raise ValueError("session_started event is required")
    settings = started.get("payload", {})
    started_at = datetime.fromisoformat(started["timestamp"])
    completed = next(
        (
            event for event in reversed(events)
            if event.get("event") == "session_completed"
        ),
        None,
    )
    completed_at = (
        datetime.fromisoformat(completed["timestamp"]) if completed else None
    )
    checkpoints = [
        datetime.fromisoformat(event["timestamp"])
        for event in events
        if event.get("event") == "capture_checkpoint"
    ]
    fatal_count = sum(
        event.get("event") in FATAL_CAPTURE_EVENTS for event in events
    )
    return observation_continuity(
        expected_duration_seconds=float(settings["duration_seconds"]),
        poll_interval_seconds=float(settings["poll_interval_seconds"]),
        started_at=started_at,
        completed_at=completed_at,
        checkpoint_timestamps=checkpoints,
        fatal_capture_errors=fatal_count,
    )
