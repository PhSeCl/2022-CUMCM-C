"""Deterministic conversion from the competition workbook to CSV files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Final

import pandas as pd

SHEET_OUTPUTS: Final[dict[str, str]] = {
    "表单1": "form_1.csv",
    "表单2": "form_2.csv",
    "表单3": "form_3.csv",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def convert_workbook(source: Path, output_dir: Path) -> dict[str, Any]:
    """Split the required workbook sheets into stable UTF-8 CSV files.

    Blank Excel cells remain blank in the CSV representation. The returned
    manifest contains content hashes and intentionally excludes timestamps so
    repeated conversion of identical input produces identical output.
    """

    source = Path(source)
    output_dir = Path(output_dir)
    if not source.is_file():
        raise FileNotFoundError(f"Workbook does not exist: {source}")

    workbook = pd.ExcelFile(source, engine="openpyxl")
    missing = [name for name in SHEET_OUTPUTS if name not in workbook.sheet_names]
    if missing:
        raise ValueError(f"Workbook is missing required sheets: {', '.join(missing)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    sheet_records: list[dict[str, Any]] = []
    for sheet_name, filename in SHEET_OUTPUTS.items():
        frame = pd.read_excel(workbook, sheet_name=sheet_name, dtype=object)
        destination = output_dir / filename
        frame.to_csv(destination, index=False, encoding="utf-8-sig", lineterminator="\n")
        sheet_records.append(
            {
                "name": sheet_name,
                "file": filename,
                "rows": len(frame),
                "columns": len(frame.columns),
                "sha256": _sha256(destination),
            }
        )

    manifest: dict[str, Any] = {
        "format_version": 1,
        "source": {"file": source.name, "sha256": _sha256(source)},
        "sheets": sheet_records,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
