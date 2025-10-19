from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from openpyxl import load_workbook

from ..utils import normalize_header
from .table_parser import build_payload


def _coerce_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        # Keep numeric text consistent with CSV path
        return ("%s" % value).strip()
    return str(value).strip()


def _detect_header_and_rows(sheet) -> Tuple[List[str], List[dict]]:
    """Find the first row that looks like a header (Pantheon exports
    often have several top rows) and return headers + data rows.
    """
    rows = list(sheet.rows)
    if not rows:
        raise ValueError("Excel fajl je prazan")

    headers: List[str] | None = None
    header_row_idx = -1

    for idx, row in enumerate(rows):
        values = [_coerce_str(c.value) for c in row]
        normalized = [normalize_header(v) for v in values]
        # Heuristic: expect at least sifra + naziv and something that looks like kolicina
        has_sifra = any(h in {"sifra", "sifra_artikla", "\u0161ifra", "\u0161ifra_artikla"} for h in normalized)
        has_naziv = any(h.startswith("naziv") for h in normalized)
        has_kolicina = any(h.startswith("kolicina") for h in normalized)
        if has_sifra and has_naziv and has_kolicina:
            headers = values
            header_row_idx = idx
            break

    if headers is None:
        # Fallback to first row as before
        headers = [_coerce_str(c.value) for c in rows[0]]
        header_row_idx = 0

    data_rows: List[dict] = []
    for row in rows[header_row_idx + 1 :]:
        values = [_coerce_str(c.value) for c in row]
        # Consider non-empty if any cell has a value
        if not any(values):
            continue
        
        # Skip rows that look like calculated values (no article code)
        # These are typically rows with only numeric values in certain columns
        has_article_code = False
        for i, header in enumerate(headers):
            if i < len(values):
                header_norm = normalize_header(header)
                if header_norm in {"sifra", "sifra_artikla", "\u0161ifra", "\u0161ifra_artikla"}:
                    if values[i].strip():  # Has article code
                        has_article_code = True
                        break
        
        # Only include rows that have article codes (main item rows)
        if has_article_code:
            record = {}
            for i, header in enumerate(headers):
                key = header if header else f"col_{i}"
                record[key] = values[i] if i < len(values) else ""
            data_rows.append(record)

    return headers, data_rows


def parse_excel(path: Path) -> dict:
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    headers, data_rows = _detect_header_and_rows(sheet)
    return build_payload(headers, data_rows, path)
