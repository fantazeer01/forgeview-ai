from __future__ import annotations

import ctypes
import platform
import re
import subprocess
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class PowerPreflight:
    platform: str
    sleep_ac_seconds: int | None
    hibernate_ac_seconds: int | None
    safe_for_overnight: bool
    warnings: tuple[str, ...]
    commands: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def inspect_windows_power(run_command=subprocess.run) -> PowerPreflight:
    if platform.system() != "Windows":
        return PowerPreflight(platform.system(), None, None, True, (), ())
    sleep = _read_ac_index(
        "SUB_SLEEP", "STANDBYIDLE", run_command=run_command
    )
    hibernate = _read_ac_index(
        "SUB_SLEEP", "HIBERNATEIDLE", run_command=run_command
    )
    warnings = []
    if sleep not in (0, None):
        warnings.append(f"AC sleep timeout is {sleep} seconds")
    if hibernate not in (0, None):
        warnings.append(f"AC hibernate timeout is {hibernate} seconds")
    if sleep is None:
        warnings.append("Unable to read AC sleep timeout")
    if hibernate is None:
        warnings.append("Unable to read AC hibernate timeout")
    commands = (
        "powercfg /change standby-timeout-ac 0",
        "powercfg /change hibernate-timeout-ac 0",
        "powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0",
        "powercfg /S SCHEME_CURRENT",
        "powercfg /getactivescheme",
        "powercfg /query SCHEME_CURRENT SUB_SLEEP",
    )
    return PowerPreflight(
        "Windows", sleep, hibernate, not warnings, tuple(warnings), commands
    )


def _read_ac_index(subgroup, setting, run_command) -> int | None:
    result = run_command(
        ["powercfg", "/query", "SCHEME_CURRENT", subgroup, setting],
        capture_output=True,
        text=True,
        errors="replace",
    )
    text = f"{result.stdout}\n{result.stderr}"
    matches = re.findall(r"0x([0-9a-fA-F]{8})", text)
    # powercfg prints current AC followed by current DC for these settings.
    return int(matches[-2], 16) if len(matches) >= 2 else None


class WindowsSleepInhibitor:
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __enter__(self):
        if platform.system() == "Windows":
            result = ctypes.windll.kernel32.SetThreadExecutionState(
                self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED
            )
            if not result:
                raise OSError("SetThreadExecutionState failed")
        return self

    def __exit__(self, exc_type, exc, tb):
        if platform.system() == "Windows":
            ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)
