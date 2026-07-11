import json
from pathlib import Path

import pandas as pd
import pytest

from cumcm2022c.data.convert import convert_workbook


def _write_complete_workbook(path: Path) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"编号": [1], "颜色": ["蓝"]}).to_excel(
            writer, sheet_name="表单1", index=False
        )
        pd.DataFrame({"采样点": ["01"], "二氧化硅(SiO2)": [90.0]}).to_excel(
            writer, sheet_name="表单2", index=False
        )
        pd.DataFrame({"文物编号": ["A1"], "二氧化硅(SiO2)": [None]}).to_excel(
            writer, sheet_name="表单3", index=False
        )


def test_convert_workbook_writes_csvs_and_stable_manifest(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    output = tmp_path / "out"
    _write_complete_workbook(source)

    first = convert_workbook(source, output)
    first_manifest_bytes = (output / "manifest.json").read_bytes()
    second = convert_workbook(source, output)

    assert sorted(path.name for path in output.glob("*.csv")) == [
        "form_1.csv",
        "form_2.csv",
        "form_3.csv",
    ]
    assert first == second
    assert first_manifest_bytes == (output / "manifest.json").read_bytes()
    assert first["source"]["sha256"]
    assert [sheet["name"] for sheet in first["sheets"]] == ["表单1", "表单2", "表单3"]
    assert "generated_at" not in first
    assert json.loads((output / "manifest.json").read_text(encoding="utf-8")) == first


def test_convert_workbook_preserves_blank_cells(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    output = tmp_path / "out"
    _write_complete_workbook(source)

    convert_workbook(source, output)

    result = pd.read_csv(output / "form_3.csv", encoding="utf-8-sig")
    assert pd.isna(result.loc[0, "二氧化硅(SiO2)"])


def test_convert_workbook_rejects_missing_sheets(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    with pd.ExcelWriter(source, engine="openpyxl") as writer:
        pd.DataFrame({"编号": [1]}).to_excel(writer, sheet_name="表单1", index=False)

    with pytest.raises(ValueError, match="表单2.*表单3"):
        convert_workbook(source, tmp_path / "out")
