from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pdfplumber

from ..utils import normalize_header


def _extract_meta_text(pages: List["pdfplumber.page.Page"]) -> str:
    text_parts: List[str] = []
    for page in pages:
        text = page.extract_text() or ""
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)


def _find_with_regex(text: str, pattern: str) -> Optional[str]:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None


def _parse_date_safe(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).isoformat()
        except ValueError:
            continue
    # fallback: just return raw if we can't parse
    return None


def _collect_items_from_tables(pages: List["pdfplumber.page.Page"]) -> List[dict]:
    items: List[dict] = []
    for page in pages:
        try:
            tables = page.extract_tables() or []
        except Exception:
            tables = []

        for rows in tables:
            if not rows or len(rows) < 2:
                continue

            # Try to detect a header row that includes sifra/naziv/kolicina
            header_row = rows[0]
            headers_norm = [normalize_header((cell or "").strip()) for cell in header_row]
            # Identify column indices
            try:
                idx_sifra = next(i for i, h in enumerate(headers_norm) if h in {"sifra", "sifra_artikla", "sifra_artikla_"})
                idx_naziv = next(i for i, h in enumerate(headers_norm) if h.startswith("naziv"))
            except StopIteration:
                # Not a product table
                continue

            # količina header can vary; fall back to last numeric-looking column
            idx_kolicina = None
            for i, h in enumerate(headers_norm):
                if h.startswith("kolicina") or h == "kolicina_tražena" or h == "kolicina_trazena":
                    idx_kolicina = i
                    break
            if idx_kolicina is None:
                # guess: pick last column
                idx_kolicina = len(header_row) - 1

            for row in rows[1:]:
                if not any(row):
                    continue
                sifra = (row[idx_sifra] or "").strip() if idx_sifra < len(row) else ""
                naziv = (row[idx_naziv] or "").strip() if idx_naziv < len(row) else ""
                kolicina_raw = (row[idx_kolicina] or "").strip() if idx_kolicina < len(row) else ""

                # Basic filtering to skip sub-total rows or separators
                if not sifra or not naziv:
                    continue
                if normalize_header(sifra) in {"red_br", "sifra", "sifra_artikla"}:
                    # another header candidate row
                    continue

                # Parse quantity
                try:
                    kolicina = float(str(kolicina_raw).replace(".", "").replace(",", "."))
                except ValueError:
                    # if it fails, skip the row
                    continue
                if kolicina <= 0:
                    continue

                items.append(
                    {
                        "artikl_sifra": sifra,
                        "naziv": naziv,
                        "kolicina_trazena": kolicina,
                        "barkod": None,
                    }
                )

    return items


def parse_pdf(path: Path) -> dict:
    """Parse Pantheon-like PDF with tabular lines.

    Attempts to extract meta (document number, date, issuer/receiver) and
    the item table (sifra, naziv, kolicina). If some meta is missing, sensible
    defaults are applied; items are mandatory.
    """
    with pdfplumber.open(path) as pdf:
        pages = pdf.pages
        text = _extract_meta_text(pages)

        # Meta extraction from header text
        dokument_broj = _find_with_regex(text, r"(^|\s)(\d{2}[-–][A-Za-z0-9]+[-–]\d{3,})(\s|$)")
        if not dokument_broj:
            # Alternative pattern: numbers with slashes or spaces
            dokument_broj = _find_with_regex(text, r"Broj\s*[:\-]?\s*([A-Za-z0-9\-/]+)")

        datum_raw = _find_with_regex(text, r"Datum\s*[:\-]?\s*(\d{2}[./]\d{2}[./]\d{4})")
        datum_iso = _parse_date_safe(datum_raw) or datetime.now().isoformat()

        magacin_name = _find_with_regex(text, r"Izdavalac\s*[:\-]?\s*(.+)") or "Nepoznati magacin"
        radnja_name = _find_with_regex(text, r"Primalac\s*[:\-]?\s*(.+)") or "Nepoznata radnja"

        # Clean potential trailing labels from captured lines
        for sep in ("\n", "  "):
            magacin_name = magacin_name.split(sep)[0].strip()
            radnja_name = radnja_name.split(sep)[0].strip()

        items = _collect_items_from_tables(pages)
        if not items:
            raise ValueError("Nisam uspio da pronađem stavke u PDF dokumentu. Provjerite format.")

    return {
        "dokument_broj": dokument_broj or None,
        "datum": datum_iso,
        "magacin_pantheon_id": normalize_header(magacin_name) or "magacin-unknown",
        "magacin_naziv": magacin_name,
        "radnja_pantheon_id": normalize_header(radnja_name) or "radnja-unknown",
        "radnja_naziv": radnja_name,
        "meta": {
            "source_file": path.name,
        },
        "stavke": items,
    }

