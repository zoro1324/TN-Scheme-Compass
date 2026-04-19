from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from data_collection.src.models import ACCEPTED_FIELDNAMES, REVIEW_FIELDNAMES, ReviewRow, SchemeRecord


def init_accepted_csv(path: str) -> None:
    _init_csv(path, ACCEPTED_FIELDNAMES)


def init_review_csv(path: str) -> None:
    _init_csv(path, REVIEW_FIELDNAMES)


def append_accepted_row(path: str, row: SchemeRecord) -> None:
    _append_rows(path, ACCEPTED_FIELDNAMES, [asdict(row)])


def append_review_row(path: str, row: ReviewRow) -> None:
    _append_rows(path, REVIEW_FIELDNAMES, [asdict(row)])


def write_accepted_csv(path: str, rows: list[SchemeRecord]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ACCEPTED_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_review_csv(path: str, rows: list[ReviewRow]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_metadata(path: str, metadata: dict[str, Any]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=True)


def _init_csv(path: str, fieldnames: list[str]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()


def _append_rows(path: str, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for row in rows:
            writer.writerow(row)
