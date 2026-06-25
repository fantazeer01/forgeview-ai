from __future__ import annotations

import csv
import json
import math
import struct
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .schema import COLUMNS, IDENTIFIER_COLUMNS, TrainingRow


def write_csv(path: Path, rows: list[TrainingRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


# Minimal standards-compliant, uncompressed Parquet writer. It intentionally
# emits one required, plain-encoded data page per column and avoids a mandatory
# third-party dependency for this local research system.
def write_parquet(path: Path, rows: list[TrainingRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dictionaries = [asdict(row) for row in rows]
    column_types: dict[str, int] = {}
    for name in COLUMNS:
        column_types[name] = 6 if name in IDENTIFIER_COLUMNS else (
            1 if name in {"early_window_flag", "late_window_flag", "outcome"} else 5
        )

    body = bytearray(b"PAR1")
    chunks: list[dict[str, int]] = []
    for name in COLUMNS if rows else ():
        parquet_type = column_types[name]
        values = [row[name] for row in dictionaries]
        encoded = _plain_values(values, parquet_type)
        page_header = _struct([
            (1, 5, _i32(0)),
            (2, 5, _i32(len(encoded))),
            (3, 5, _i32(len(encoded))),
            (5, 12, _struct([
                (1, 5, _i32(len(values))),
                (2, 5, _i32(0)),
                (3, 5, _i32(3)),
                (4, 5, _i32(3)),
            ])),
        ])
        offset = len(body)
        body.extend(page_header)
        body.extend(encoded)
        total = len(page_header) + len(encoded)
        chunks.append({"offset": offset, "total": total, "type": parquet_type})

    schema = [_struct([(4, 8, _binary("schema")), (5, 5, _i32(len(COLUMNS)))])]
    for name in COLUMNS:
        fields = [
            (1, 5, _i32(column_types[name])),
            (3, 5, _i32(0)),
            (4, 8, _binary(name)),
        ]
        if column_types[name] == 6:
            fields.append((6, 5, _i32(0)))
        schema.append(_struct(fields))

    columns = []
    for name, chunk in zip(COLUMNS, chunks):
        metadata = _struct([
            (1, 5, _i32(chunk["type"])),
            (2, 9, _list(5, [_i32(0), _i32(3)])),
            (3, 9, _list(8, [_binary(name)])),
            (4, 5, _i32(0)),
            (5, 6, _i64(len(rows))),
            (6, 6, _i64(chunk["total"])),
            (7, 6, _i64(chunk["total"])),
            (9, 6, _i64(chunk["offset"])),
        ])
        columns.append(_struct([
            (2, 6, _i64(chunk["offset"])),
            (3, 12, metadata),
        ]))
    row_groups = []
    if rows:
        row_groups.append(_struct([
            (1, 9, _list(12, columns)),
            (2, 6, _i64(sum(chunk["total"] for chunk in chunks))),
            (3, 6, _i64(len(rows))),
        ]))
    footer = _struct([
        (1, 5, _i32(1)),
        (2, 9, _list(12, schema)),
        (3, 6, _i64(len(rows))),
        (4, 9, _list(12, row_groups)),
        (6, 8, _binary("ForgeViewAI Feature Engine v1")),
    ])
    body.extend(footer)
    body.extend(struct.pack("<I", len(footer)))
    body.extend(b"PAR1")
    path.write_bytes(body)


def _plain_values(values: list[Any], parquet_type: int) -> bytes:
    if parquet_type == 6:
        return b"".join(
            struct.pack("<I", len(encoded)) + encoded
            for encoded in (str(value or "").encode("utf-8") for value in values)
        )
    if parquet_type == 1:
        return b"".join(struct.pack("<i", int(value or 0)) for value in values)
    return b"".join(
        struct.pack("<d", float(value) if value is not None else math.nan)
        for value in values
    )


def _varint(value: int) -> bytes:
    output = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        output.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(output)


def _zigzag(value: int) -> int:
    return (value << 1) ^ (value >> 63)


def _i32(value: int) -> bytes:
    return _varint(_zigzag(value))


def _i64(value: int) -> bytes:
    return _varint(_zigzag(value))


def _binary(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return _varint(len(encoded)) + encoded


def _list(element_type: int, values: list[bytes]) -> bytes:
    size = len(values)
    header = bytes([(size << 4) | element_type]) if size < 15 else (
        bytes([(15 << 4) | element_type]) + _varint(size)
    )
    return header + b"".join(values)


def _struct(fields: list[tuple[int, int, bytes]]) -> bytes:
    output = bytearray()
    previous = 0
    for field_id, compact_type, payload in sorted(fields):
        delta = field_id - previous
        if 0 < delta <= 15:
            output.append((delta << 4) | compact_type)
        else:
            output.append(compact_type)
            output.extend(_i32(field_id))
        output.extend(payload)
        previous = field_id
    output.append(0)
    return bytes(output)
