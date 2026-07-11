"""Stable loading interface for machine-readable competition tables."""

from pathlib import Path
from typing import Final, Literal

import pandas as pd

TableName = Literal["form_1", "form_2", "form_3"]
TABLE_FILES: Final[dict[str, str]] = {
    "form_1": "form_1.csv",
    "form_2": "form_2.csv",
    "form_3": "form_3.csv",
}


def load_table(name: TableName | str, data_dir: Path = Path("data/raw")) -> pd.DataFrame:
    """Load one converted table without filling its missing values."""

    if name not in TABLE_FILES:
        allowed = ", ".join(TABLE_FILES)
        raise ValueError(f"Unknown table {name!r}; expected one of: {allowed}")
    path = Path(data_dir) / TABLE_FILES[name]
    if not path.is_file():
        raise FileNotFoundError(f"Converted table does not exist: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")
