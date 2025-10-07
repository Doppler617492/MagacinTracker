from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from .table_parser import build_payload


def parse_excel(path: Path) -> dict:
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    rows = list(sheet.rows)
    if not rows:
        raise ValueError("Excel fajl je prazan")

    headers = [str(cell.value or "").strip() for cell in rows[0]]
    data_rows = []
    for row in rows[1:]:
        data = {}
        for index, cell in enumerate(row):
            header = headers[index] if index < len(headers) else f"col_{index}"
            value = cell.value
            if isinstance(value, str):
                value = value.strip()
            data[header] = str(value) if value is not None else ""
        if any(value for value in data.values()):
            data_rows.append(data)

    return build_payload(headers, data_rows, path)
