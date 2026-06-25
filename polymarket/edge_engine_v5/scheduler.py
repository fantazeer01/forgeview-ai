from __future__ import annotations

import math
import time
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterator


class CaptureScheduler:
    """Produces deterministic mock timestamps or wall-clock public timestamps."""

    def __init__(
        self,
        duration_seconds: float,
        poll_interval_seconds: float,
        mock: bool,
        mock_start: datetime | None = None,
        utc_now: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.duration_seconds = duration_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.mock = mock
        self.mock_start = mock_start or datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.utc_now = utc_now or (lambda: datetime.now(timezone.utc))
        self.monotonic = monotonic or time.monotonic
        self.sleep = sleep or time.sleep
        self.started_monotonic: float | None = None
        self.ended_monotonic: float | None = None
        self.clock_discontinuities: list[dict[str, float | str]] = []

    def ticks(self) -> Iterator[tuple[int, datetime]]:
        if self.mock:
            iterations = max(
                2, math.ceil(self.duration_seconds / self.poll_interval_seconds)
            )
            self.started_monotonic = 0.0
            for index in range(iterations):
                yield index, self.mock_start + timedelta(
                    seconds=index * self.poll_interval_seconds
                )
            self.ended_monotonic = self.duration_seconds
            return

        self.started_monotonic = self.monotonic()
        start_utc = self.utc_now()
        index = 0
        deadline = self.started_monotonic
        while True:
            now_monotonic = self.monotonic()
            elapsed = now_monotonic - self.started_monotonic
            if index > 0 and elapsed >= self.duration_seconds:
                break
            timestamp = self.utc_now()
            utc_elapsed = (timestamp - start_utc).total_seconds()
            drift = utc_elapsed - elapsed
            if abs(drift) > max(1.0, self.poll_interval_seconds):
                previous = self.clock_discontinuities[-1] if self.clock_discontinuities else None
                if previous is None or abs(float(previous["drift_seconds"]) - drift) > 0.001:
                    self.clock_discontinuities.append({
                        "timestamp": timestamp.isoformat(),
                        "monotonic_elapsed_seconds": round(elapsed, 6),
                        "utc_elapsed_seconds": round(utc_elapsed, 6),
                        "drift_seconds": round(drift, 6),
                    })
            yield index, timestamp
            index += 1
            deadline = self.started_monotonic + index * self.poll_interval_seconds
            remaining = self.duration_seconds - (self.monotonic() - self.started_monotonic)
            if remaining <= 0:
                break
            wait = min(max(0.0, deadline - self.monotonic()), remaining)
            if wait:
                self.sleep(wait)
        self.ended_monotonic = self.monotonic()

    @property
    def elapsed_seconds(self) -> float:
        if self.started_monotonic is None or self.ended_monotonic is None:
            return 0.0
        return max(0.0, self.ended_monotonic - self.started_monotonic)


def discovery_due(
    timestamp: datetime,
    previous: datetime | None,
    interval_seconds: float,
) -> bool:
    return previous is None or (timestamp - previous).total_seconds() >= interval_seconds
