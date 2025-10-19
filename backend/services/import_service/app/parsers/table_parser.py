from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from ..utils import normalize_header

REQUIRED_ITEM_FIELDS = {"artikl_sifra", "naziv", "kolicina"}

COLUMN_ALIASES = {
    "dokument_broj": ["broj dokumenta", "broj", "dokument"],
    "datum": ["datum"],
    "magacin": ["izvor", "magacin", "magacin naziv"],
    "radnja": ["odredište", "radnja", "lokacija"],
    "artikl_sifra": ["šifra artikla", "sifra artikla", "šifra", "sifra", "Šifra", "Šifra artikla"],
    "naziv": ["naziv artikla", "naziv", "Naziv"],
    "kolicina": ["količina", "kolicina", "kolicina trazena", "Količina"],
    "barkod": ["barkod", "barcode"],
}


def _map_headers(headers: Iterable[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    normalized = {normalize_header(header): header for header in headers}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = normalize_header(alias)
            if key in normalized:
                mapping[target] = normalized[key]
                break
    return mapping


def _parse_date(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(raw)


def build_payload(headers: List[str], rows: List[dict], file_path: Path) -> dict:
    if not rows:
        raise ValueError("Fajl ne sadrži podatke")

    mapping = _map_headers(headers)
    first_row = rows[0]
    dokument_broj = first_row.get(mapping.get("dokument_broj", ""), "").strip()
    datum_raw = first_row.get(mapping.get("datum", ""), "").strip()
    magacin_name = first_row.get(mapping.get("magacin", ""), "").strip() or "Nepoznati magacin"
    radnja_name = first_row.get(mapping.get("radnja", ""), "").strip() or "Nepoznata radnja"

    # If no document metadata found in data rows, try to extract from file name
    if not dokument_broj and file_path.name:
        # Extract document number from filename like "MP kalkulacija za knjigovodstvo_25-20AT-000336.xlsx"
        import re
        match = re.search(r'(\d+-\d+[A-Z]+-\d+)', file_path.name)
        if match:
            dokument_broj = match.group(1)
    
    # Set default values if not found
    if not dokument_broj:
        dokument_broj = f"IMPORT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    if not magacin_name or magacin_name == "Nepoznati magacin":
        magacin_name = "Veleprodajni Magacin"
    if not radnja_name or radnja_name == "Nepoznata radnja":
        radnja_name = "Tranzitno Skladiste"

    datum = _parse_date(datum_raw) if datum_raw else datetime.now()

    items: List[dict] = []
    for index, row in enumerate(rows, start=1):
        item_data = {}
        for field in REQUIRED_ITEM_FIELDS.union({"barkod"}):
            column = mapping.get(field)
            item_data[field] = row.get(column, "").strip() if column else ""

        if not item_data["artikl_sifra"]:
            raise ValueError(f"Nedostaje šifra artikla u redu {index}")
        if not item_data["naziv"]:
            raise ValueError(f"Nedostaje naziv artikla za šifru {item_data['artikl_sifra']}")
        try:
            quantity = float(item_data["kolicina"].replace(",", "."))
        except ValueError as exc:  # noqa: BLE001
            raise ValueError(f"Neispravna količina u redu {index}") from exc
        if quantity <= 0:
            raise ValueError(f"Količina mora biti veća od 0 (red {index})")

        items.append(
            {
                "artikl_sifra": item_data["artikl_sifra"],
                "naziv": item_data["naziv"],
                "kolicina_trazena": quantity,
                "barkod": item_data.get("barkod") or None,
            }
        )

    file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    if not dokument_broj:
        dokument_broj = f"NO-DOC-{file_hash[:8]}"

    return {
        "dokument_broj": dokument_broj,
        "datum": datum.isoformat(),
        "magacin_pantheon_id": normalize_header(magacin_name) or "magacin-unknown",
        "magacin_naziv": magacin_name,
        "radnja_pantheon_id": normalize_header(radnja_name) or "radnja-unknown",
        "radnja_naziv": radnja_name,
        "meta": {
            "file_hash": file_hash,
        },
        "stavke": items,
    }
