from __future__ import annotations

from polymarket.feature_engine.schema import COLUMNS, TrainingRow


def public_only(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("market_source") == "public"]


def to_training_rows(rows: list[dict[str, str]]) -> list[TrainingRow]:
    return [TrainingRow(**{
        column: _coerce(column, row.get(column, ""))
        for column in COLUMNS
    }) for row in rows]


def _coerce(column: str, value: str):
    if column in {
        "market_id", "asset", "market_source", "window_start", "window_end",
        "feature_timestamp", "resolution_timestamp", "label_source",
        "source_session",
    }:
        return value
    if column in {"early_window_flag", "late_window_flag", "outcome"}:
        return int(value)
    return None if value == "" else float(value)
