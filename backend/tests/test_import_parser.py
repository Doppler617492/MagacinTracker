from pathlib import Path

import pytest

from services.import_service.app.parsers.csv_parser import parse_csv


def write_tmp_csv(tmp_path: Path, content: str) -> Path:
    file_path = tmp_path / "import.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_parse_csv_success(tmp_path: Path) -> None:
    csv_content = """Broj dokumenta,Datum,Izvor,Odredište,Šifra artikla,Naziv artikla,Količina
25-20CT-000279,03.10.2025,Veleprodajni Magacin,Prodavnica - Kotor Centar,200431,Jastuk KING,24
"""
    path = write_tmp_csv(tmp_path, csv_content)

    result = parse_csv(path)

    assert result["dokument_broj"] == "25-20CT-000279"
    assert result["magacin_pantheon_id"] == "veleprodajni_magacin"
    assert result["radnja_pantheon_id"] == "prodavnica_kotor_centar"
    assert len(result["stavke"]) == 1
    assert result["stavke"][0]["artikl_sifra"] == "200431"


def test_parse_csv_invalid_quantity(tmp_path: Path) -> None:
    csv_content = """Broj dokumenta,Datum,Izvor,Odredište,Šifra artikla,Naziv artikla,Količina
25-20CT-000279,03.10.2025,Veleprodajni Magacin,Prodavnica - Kotor Centar,200431,Jastuk KING,-1
"""
    path = write_tmp_csv(tmp_path, csv_content)

    with pytest.raises(ValueError):
        parse_csv(path)
