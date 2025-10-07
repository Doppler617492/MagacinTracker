from __future__ import annotations

import csv
from pathlib import Path

from .table_parser import build_payload


def _dialect_for_file(path: Path) -> csv.Dialect:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        sample = handle.read(2048)
        try:
            return csv.Sniffer().sniff(sample)
        except csv.Error:
            return csv.get_dialect("excel")


def parse_csv(path: Path) -> dict:
    dialect = _dialect_for_file(path)
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        headers = reader.fieldnames or []
        rows = list(reader)

    return build_payload(headers, rows, path)
