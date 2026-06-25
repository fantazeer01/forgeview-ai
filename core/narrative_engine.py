"""Stateful serialization layer for ForgeView Probability Lab episodes."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(r"D:\ForgeViewAI")
SEASON_ID = "S1"
SEASON_THEME = (
    "Does a real trading edge exist in Polymarket BTC 5m markets "
    "or is it a data illusion?"
)
ATTENTION_STAGES = ("hook", "breakdown", "partial_resolution", "open_loop_question")
DEFAULT_STATE_PATH = WORKSPACE_ROOT / "state" / "episode_state.json"


class NarrativeError(ValueError):
    """Raised when an episode would break serialized continuity."""


def ensure_workspace_path(path: Path | str) -> Path:
    resolved = Path(path).resolve()
    root = WORKSPACE_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise NarrativeError(f"path must stay inside {root}: {resolved}")
    return resolved


@dataclass
class EpisodeState:
    episode_id: str = "S1E00"
    season_id: str = SEASON_ID
    season_theme: str = SEASON_THEME
    belief_state: str = (
        "An apparent predictive edge exists, but real executable profitability "
        "has not been confirmed."
    )
    open_loop: str = (
        "Will the apparent edge survive enough real captured buying prices "
        "to separate profit from data illusion?"
    )
    contradiction_chain: list[str] = field(
        default_factory=lambda: [
            "Predictive improvement did not prove executable profit.",
            "Simulated profit relied on prices that were not captured live.",
            "The first real-price result was positive but used only two trades.",
        ]
    )
    last_result: str = "Real ask edge remains not confirmed."
    next_trigger: str = "Generate the next episode from the current open loop."
    continuation_required: bool = True
    updated_at: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EpisodeState":
        state = cls()
        for key in asdict(state):
            if key in raw:
                setattr(state, key, deepcopy(raw[key]))
        validate_state(state)
        return state


def validate_state(state: EpisodeState) -> None:
    if state.season_id != SEASON_ID:
        raise NarrativeError(f"season cannot reset or change from {SEASON_ID}")
    if state.season_theme != SEASON_THEME:
        raise NarrativeError("season theme cannot change")
    if not re.fullmatch(r"S1E\d{2,}", state.episode_id):
        raise NarrativeError(f"invalid episode_id: {state.episode_id}")
    if not state.belief_state.strip():
        raise NarrativeError("belief_state is required")
    if not state.open_loop.strip().endswith("?"):
        raise NarrativeError("open_loop must be an unresolved question")
    if not state.contradiction_chain:
        raise NarrativeError("contradiction_chain cannot be empty")
    if state.continuation_required is not True:
        raise NarrativeError("continuation_required must remain true")


def next_episode_id(current: str) -> str:
    match = re.fullmatch(r"S1E(\d+)", current)
    if not match:
        raise NarrativeError(f"invalid current episode_id: {current}")
    return f"S1E{int(match.group(1)) + 1:02d}"


class StateStore:
    def __init__(self, path: Path | str = DEFAULT_STATE_PATH):
        self.path = ensure_workspace_path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def load(self) -> EpisodeState:
        if not self.path.exists():
            return EpisodeState()
        return EpisodeState.from_dict(json.loads(self.path.read_text(encoding="utf-8")))

    def save(self, state: EpisodeState, lock_timeout: float = 10.0) -> None:
        validate_state(state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        descriptor = None
        while descriptor is None:
            try:
                descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if time.monotonic() - started >= lock_timeout:
                    raise TimeoutError(f"state lock timeout: {self.lock_path}")
                time.sleep(0.05)
        try:
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            os.close(descriptor)
            descriptor = None
            payload = json.dumps(asdict(state), indent=2, ensure_ascii=True) + "\n"
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=self.path.name + ".",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(payload)
                temp_path = Path(handle.name)
            os.replace(temp_path, self.path)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            self.lock_path.unlink(missing_ok=True)


def prepare_episode(
    state: EpisodeState,
    research_event: dict[str, Any],
) -> dict[str, Any]:
    """Create mandatory narrative context before any channel output is generated."""
    validate_state(state)
    event_name = str(research_event.get("research_event") or research_event.get("event") or "").strip()
    result = str(research_event.get("result") or research_event.get("last_result") or "").strip()
    contradiction = str(research_event.get("contradiction") or "").strip()
    if not event_name or not result or not contradiction:
        raise NarrativeError("research_event, result, and contradiction are required")

    episode_id = next_episode_id(state.episode_id)
    return {
        "season_id": state.season_id,
        "season_theme": state.season_theme,
        "episode_id": episode_id,
        "depends_on_episode": state.episode_id,
        "previous_belief_state": state.belief_state,
        "previous_open_loop": state.open_loop,
        "previous_result": state.last_result,
        "contradiction_chain": [*state.contradiction_chain, contradiction],
        "current_research_event": event_name,
        "current_result": result,
        "required_contradiction": contradiction,
        "attention_structure": {
            "hook": "Open with the contradiction in the first two seconds.",
            "breakdown": "Show the system failure or insight shift.",
            "partial_resolution": "Resolve only part of the previous open loop.",
            "open_loop_question": "End with a new unresolved question.",
        },
        "generation_rules": {
            "must_depend_on_previous_episode": True,
            "must_update_belief_state": True,
            "must_create_new_open_loop": True,
            "must_end_with_question": True,
            "may_resolve_core_season_question": False,
            "continuation_required": True,
        },
        "continuation_required": True,
    }


def validate_generated_episode(
    prepared: dict[str, Any],
    generated: dict[str, Any],
) -> None:
    required = {
        "episode_id",
        "narrative_hook",
        "breakdown",
        "partial_resolution",
        "belief_state",
        "open_loop",
        "last_result",
    }
    missing = sorted(key for key in required if not str(generated.get(key, "")).strip())
    if missing:
        raise NarrativeError(f"generated episode missing fields: {', '.join(missing)}")
    if generated["episode_id"] != prepared["episode_id"]:
        raise NarrativeError("generated episode_id does not match prepared transition")
    if not generated["open_loop"].strip().endswith("?"):
        raise NarrativeError("generated open_loop must end with a question")
    if generated["open_loop"].strip() == prepared["previous_open_loop"].strip():
        raise NarrativeError("episode must create a new open_loop")
    if generated["belief_state"].strip() == prepared["previous_belief_state"].strip():
        raise NarrativeError("episode must evolve belief_state")
    if SEASON_THEME.lower() in generated["last_result"].lower():
        raise NarrativeError("episode cannot fully resolve the core season question")


def commit_episode(
    state: EpisodeState,
    prepared: dict[str, Any],
    generated: dict[str, Any],
) -> EpisodeState:
    """Advance state only after all narrative requirements pass validation."""
    validate_state(state)
    validate_generated_episode(prepared, generated)
    if prepared["depends_on_episode"] != state.episode_id:
        raise NarrativeError("stale state: another episode advanced before commit")
    contradiction = prepared["required_contradiction"]
    chain = [*state.contradiction_chain]
    if contradiction not in chain:
        chain.append(contradiction)
    return EpisodeState(
        episode_id=prepared["episode_id"],
        season_id=state.season_id,
        season_theme=state.season_theme,
        belief_state=generated["belief_state"].strip(),
        open_loop=generated["open_loop"].strip(),
        contradiction_chain=chain,
        last_result=generated["last_result"].strip(),
        next_trigger=str(
            generated.get("next_trigger")
            or f"Investigate: {generated['open_loop'].strip()}"
        ),
        continuation_required=True,
        updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


def extend_execution_bundle(
    bundle: dict[str, Any],
    state: EpisodeState,
    narrative_hook: str,
) -> dict[str, Any]:
    """Add top-level narrative fields without changing existing bundle fields."""
    validate_state(state)
    extended = deepcopy(bundle)
    extended.update(
        {
            "season_id": state.season_id,
            "episode_id": state.episode_id,
            "belief_state": state.belief_state,
            "open_loop": state.open_loop,
            "contradiction_chain": deepcopy(state.contradiction_chain),
            "last_result": state.last_result,
            "narrative_hook": narrative_hook,
            "continuation_required": True,
        }
    )
    return extended


def _read_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="ForgeView serialized episode engine")
    parser.add_argument("--state", default=str(DEFAULT_STATE_PATH))
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--event", required=True)
    prepare_parser.add_argument("--out")

    commit_parser = subparsers.add_parser("commit")
    commit_parser.add_argument("--prepared", required=True)
    commit_parser.add_argument("--generated", required=True)

    bundle_parser = subparsers.add_parser("extend-bundle")
    bundle_parser.add_argument("--bundle", required=True)
    bundle_parser.add_argument("--hook", required=True)
    bundle_parser.add_argument("--out", required=True)

    args = parser.parse_args()
    store = StateStore(args.state)
    state = store.load()

    if args.command == "prepare":
        result = prepare_episode(state, _read_json(args.event))
        payload = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
        if args.out:
            ensure_workspace_path(args.out).write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
    elif args.command == "commit":
        updated = commit_episode(
            state,
            _read_json(args.prepared),
            _read_json(args.generated),
        )
        store.save(updated)
        print(json.dumps(asdict(updated), indent=2, ensure_ascii=True))
    elif args.command == "extend-bundle":
        extended = extend_execution_bundle(_read_json(args.bundle), state, args.hook)
        ensure_workspace_path(args.out).write_text(
            json.dumps(extended, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
