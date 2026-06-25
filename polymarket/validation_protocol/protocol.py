from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


LABEL_COLUMNS = ("outcome", "resolution_timestamp", "label_source")
HOLDOUT_LABEL_COLUMNS = ("market_id",) + LABEL_COLUMNS
ASSIGNMENT_COLUMNS = (
    "market_id", "asset", "window_start", "window_end", "assignment", "reason",
)


@dataclass(frozen=True)
class ProtocolConfig:
    dataset_path: Path = Path("polymarket/data/training/public_only.csv")
    output_root: Path = Path("polymarket/data/validation_protocol/v1")
    train_fraction: float = 0.70
    validation_fraction: float = 0.15
    holdout_fraction: float = 0.15
    purge_windows: int = 1
    embargo_windows: int = 1

    def __post_init__(self) -> None:
        if round(
            self.train_fraction + self.validation_fraction + self.holdout_fraction,
            12,
        ) != 1.0:
            raise ValueError("split fractions must sum to 1")
        if min(
            self.train_fraction,
            self.validation_fraction,
            self.holdout_fraction,
        ) <= 0:
            raise ValueError("split fractions must be positive")
        if self.purge_windows < 1 or self.embargo_windows < 1:
            raise ValueError("purge and embargo must each remove at least one window")


class ValidationProtocol:
    """Build and verify immutable, chronological development/holdout splits."""

    def __init__(self, config: ProtocolConfig | None = None) -> None:
        self.config = config or ProtocolConfig()

    def freeze(self) -> dict[str, Any]:
        fields, rows = _read_csv(self.config.dataset_path)
        _validate_source(fields, rows)
        rows.sort(key=_row_key)
        groups = _window_groups(rows)
        assignments, boundaries = self._assign(groups)

        train = _assigned_rows(groups, assignments, "train")
        validation = _assigned_rows(groups, assignments, "validation")
        holdout = _assigned_rows(groups, assignments, "holdout")
        excluded = _assigned_rows(groups, assignments, "excluded")
        output = self.config.output_root
        output.mkdir(parents=True, exist_ok=True)

        artifact_rows: dict[str, tuple[tuple[str, ...], list[dict[str, str]]]] = {
            "train.csv": (tuple(fields), train),
            "validation.csv": (tuple(fields), validation),
            "holdout_features.csv": (
                tuple(name for name in fields if name not in LABEL_COLUMNS),
                [{k: v for k, v in row.items() if k not in LABEL_COLUMNS}
                 for row in holdout],
            ),
            "sealed_holdout_labels.csv": (
                HOLDOUT_LABEL_COLUMNS,
                [{name: row[name] for name in HOLDOUT_LABEL_COLUMNS}
                 for row in holdout],
            ),
            "excluded_boundary_rows.csv": (
                tuple(fields) + ("assignment_reason",),
                [
                    {
                        **row,
                        "assignment_reason": assignments[row["window_start"]][1],
                    }
                    for row in excluded
                ],
            ),
            "split_assignments.csv": (
                ASSIGNMENT_COLUMNS,
                [
                    {
                        "market_id": row["market_id"],
                        "asset": row["asset"],
                        "window_start": row["window_start"],
                        "window_end": row["window_end"],
                        "assignment": assignments[row["window_start"]][0],
                        "reason": assignments[row["window_start"]][1],
                    }
                    for row in rows
                ],
            ),
        }
        for name, (columns, values) in artifact_rows.items():
            _write_csv(output / name, columns, values)

        manifest = self._manifest(
            fields, rows, groups, assignments, boundaries, artifact_rows
        )
        _write_json(output / "protocol_manifest.json", manifest)
        return manifest

    def inspect(self) -> dict[str, Any]:
        manifest = _load_manifest(self.config.output_root)
        # Deliberately expose only the label commitment, never holdout outcomes.
        return manifest

    def verify(self) -> dict[str, Any]:
        manifest = _load_manifest(self.config.output_root)
        source = self.config.dataset_path
        if _sha256(source) != manifest["source"]["sha256"]:
            raise ValueError("source dataset hash differs from frozen protocol")
        for name, expected in manifest["artifacts"].items():
            path = self.config.output_root / name
            if not path.exists() or _sha256(path) != expected["sha256"]:
                raise ValueError(f"artifact hash mismatch: {name}")
        assignments = _read_csv(
            self.config.output_root / "split_assignments.csv"
        )[1]
        _verify_assignments(assignments, manifest)
        return manifest

    def _assign(
        self, groups: dict[str, list[dict[str, str]]]
    ) -> tuple[dict[str, tuple[str, str]], dict[str, Any]]:
        windows = sorted(groups)
        required = (
            2 * (self.config.purge_windows + self.config.embargo_windows) + 3
        )
        if len(windows) < required:
            raise ValueError(
                f"at least {required} distinct windows are required; got {len(windows)}"
            )
        first_cut = int(len(windows) * self.config.train_fraction)
        second_cut = int(
            len(windows)
            * (self.config.train_fraction + self.config.validation_fraction)
        )
        assignments = {
            window: (
                "train" if index < first_cut else
                "validation" if index < second_cut else
                "holdout",
                "chronological_split",
            )
            for index, window in enumerate(windows)
        }
        boundary_data = []
        for name, cut in (
            ("train_validation", first_cut),
            ("validation_holdout", second_cut),
        ):
            for index in range(
                max(0, cut - self.config.purge_windows), cut
            ):
                assignments[windows[index]] = (
                    "excluded", f"{name}_purge"
                )
            for index in range(
                cut, min(len(windows), cut + self.config.embargo_windows)
            ):
                assignments[windows[index]] = (
                    "excluded", f"{name}_embargo"
                )
            boundary_data.append({
                "name": name,
                "raw_cut_window": windows[cut],
                "last_development_window": _last_assigned(
                    windows, assignments,
                    "train" if name == "train_validation" else "validation",
                    before=cut,
                ),
                "first_next_window": _first_assigned(
                    windows, assignments,
                    "validation" if name == "train_validation" else "holdout",
                    after=cut,
                ),
                "purged_windows": windows[
                    max(0, cut - self.config.purge_windows):cut
                ],
                "embargoed_windows": windows[
                    cut:min(len(windows), cut + self.config.embargo_windows)
                ],
            })
        return assignments, {"boundaries": boundary_data}

    def _manifest(
        self,
        fields: list[str],
        rows: list[dict[str, str]],
        groups: dict[str, list[dict[str, str]]],
        assignments: dict[str, tuple[str, str]],
        boundaries: dict[str, Any],
        artifact_rows: dict[
            str, tuple[tuple[str, ...], list[dict[str, str]]]
        ],
    ) -> dict[str, Any]:
        counts = {
            split: sum(
                len(groups[window])
                for window, (assignment, _) in assignments.items()
                if assignment == split
            )
            for split in ("train", "validation", "holdout", "excluded")
        }
        window_counts = {
            split: sum(
                assignment == split
                for assignment, _ in assignments.values()
            )
            for split in ("train", "validation", "holdout", "excluded")
        }
        artifacts = {}
        for name, (_, values) in artifact_rows.items():
            path = self.config.output_root / name
            artifacts[name] = {
                "sha256": _sha256(path),
                "row_count": len(values),
            }
        label_path = self.config.output_root / "sealed_holdout_labels.csv"
        return {
            "schema_version": 1,
            "protocol_id": "time_ordered_holdout_v1",
            "status": "frozen",
            "source": {
                "path": str(self.config.dataset_path),
                "sha256": _sha256(self.config.dataset_path),
                "row_count": len(rows),
                "window_count": len(groups),
                "first_window": min(groups),
                "last_window": max(groups),
                "required_market_source": "public",
                "required_label_source": "polymarket_gamma_resolved",
                "columns": fields,
            },
            "configuration": {
                "train_fraction": self.config.train_fraction,
                "validation_fraction": self.config.validation_fraction,
                "holdout_fraction": self.config.holdout_fraction,
                "atomic_unit": "window_start",
                "purge_windows_per_boundary": self.config.purge_windows,
                "embargo_windows_per_boundary": self.config.embargo_windows,
                "window_duration_seconds": 300,
            },
            "splits": {
                "row_counts": counts,
                "window_counts": window_counts,
                **boundaries,
            },
            "holdout": {
                "labels_sealed": True,
                "development_api_exposes_labels": False,
                "label_commitment_sha256": _sha256(label_path),
                "selection_use_prohibited": True,
                "release_condition": (
                    "one-time final evaluation after candidate and thresholds "
                    "are frozen from train/validation only"
                ),
            },
            "baselines": {
                "unconditional_frequency": (
                    "training-split UP frequency, constant probability"
                ),
                "polymarket_probability": "row yes_price",
                "deterministic_lag_score": (
                    "existing lag_score transformed by a rule fitted on train only"
                ),
                "logistic_regression": (
                    "interpretable regularized linear probability baseline; "
                    "preprocessing fitted on train only"
                ),
            },
            "metrics": {
                "primary": ["log_loss", "brier_score"],
                "secondary": [
                    "calibration_error", "balanced_accuracy", "roc_auc",
                    "precision", "recall", "asset_attribution",
                    "time_period_attribution",
                ],
            },
            "precommitted_acceptance": {
                "validation_advancement": [
                    "candidate beats unconditional frequency on both primary metrics",
                    "candidate improves at least one primary metric versus Polymarket by >=1%",
                    "the other primary metric is no worse than Polymarket by >0.5%",
                    "directional benefit is present in at least two assets",
                ],
                "final_holdout_edge_evidence": [
                    "frozen candidate beats both unconditional and Polymarket baselines on log loss",
                    "frozen candidate beats both unconditional and Polymarket baselines on Brier score",
                    "relative improvement versus Polymarket is >=1% on both primary metrics",
                    "benefit is present in at least two assets and no single asset supplies >40% of simulated net P&L",
                    "cost and latency stress tests remain positive",
                ],
                "holdout_reuse": "prohibited",
            },
            "artifacts": artifacts,
        }


def load_development_rows(
    output_root: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Load train/validation only; holdout is intentionally absent."""
    train = _read_csv(output_root / "train.csv")[1]
    validation = _read_csv(output_root / "validation.csv")[1]
    return train, validation


def _validate_source(fields: list[str], rows: list[dict[str, str]]) -> None:
    required = {
        "market_id", "asset", "market_source", "window_start", "window_end",
        "feature_timestamp", "outcome", "resolution_timestamp", "label_source",
    }
    missing = required - set(fields)
    if missing:
        raise ValueError(f"dataset missing columns: {sorted(missing)}")
    if not rows:
        raise ValueError("dataset is empty")
    if any(row["market_source"] != "public" for row in rows):
        raise ValueError("protocol accepts public rows only")
    if any(
        row["label_source"] != "polymarket_gamma_resolved" for row in rows
    ):
        raise ValueError("protocol accepts authoritative labels only")
    ids = [row["market_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate market_id values are not allowed")
    for row in rows:
        start = _dt(row["window_start"])
        end = _dt(row["window_end"])
        feature = _dt(row["feature_timestamp"])
        if not start <= feature < end:
            raise ValueError(f"feature timestamp outside market window: {row['market_id']}")
        if (end - start).total_seconds() != 300:
            raise ValueError(f"market is not a five-minute window: {row['market_id']}")


def _window_groups(
    rows: list[dict[str, str]]
) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["window_start"]].append(row)
    ordered = sorted(groups)
    for previous, current in zip(ordered, ordered[1:]):
        previous_end = max(
            _dt(row["window_end"]) for row in groups[previous]
        )
        if previous_end > _dt(current):
            raise ValueError(
                f"overlapping atomic windows: {previous} and {current}"
            )
    return dict(groups)


def _assigned_rows(groups, assignments, split):
    return sorted(
        [
            row
            for window, values in groups.items()
            if assignments[window][0] == split
            for row in values
        ],
        key=_row_key,
    )


def _verify_assignments(
    assignments: list[dict[str, str]], manifest: dict[str, Any]
) -> None:
    if len(assignments) != manifest["source"]["row_count"]:
        raise ValueError("assignment row count differs from source")
    ids = [row["market_id"] for row in assignments]
    if len(ids) != len(set(ids)):
        raise ValueError("a market appears in more than one assignment")
    allowed = {"train", "validation", "holdout", "excluded"}
    if any(row["assignment"] not in allowed for row in assignments):
        raise ValueError("unknown split assignment")
    order = {"train": 0, "validation": 1, "holdout": 2}
    active = [
        row for row in assignments if row["assignment"] != "excluded"
    ]
    ranks = [order[row["assignment"]] for row in active]
    if ranks != sorted(ranks):
        raise ValueError("split assignments are not chronological")
    grouped: dict[str, set[str]] = defaultdict(set)
    for row in assignments:
        grouped[row["window_start"]].add(row["assignment"])
    if any(len(values) != 1 for values in grouped.values()):
        raise ValueError("an atomic window crosses split boundaries")


def _last_assigned(windows, assignments, split, before):
    matches = [
        window for window in windows[:before]
        if assignments[window][0] == split
    ]
    return matches[-1] if matches else None


def _first_assigned(windows, assignments, split, after):
    matches = [
        window for window in windows[after:]
        if assignments[window][0] == split
    ]
    return matches[0] if matches else None


def _row_key(row: dict[str, str]):
    return row["window_start"], row["asset"], row["market_id"]


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or ()), list(reader)


def _write_csv(
    path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=columns, lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / "protocol_manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"frozen protocol not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
