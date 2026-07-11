from pathlib import Path

import pandas as pd
import pytest

from cumcm2022c.data.load import load_table


def test_load_table_reads_known_form(tmp_path: Path) -> None:
    pd.DataFrame({"编号": [1]}).to_csv(
        tmp_path / "form_1.csv", index=False, encoding="utf-8-sig"
    )

    result = load_table("form_1", tmp_path)

    assert result.to_dict(orient="records") == [{"编号": 1}]


def test_load_table_rejects_unknown_form(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="form_1, form_2, form_3"):
        load_table("unknown", tmp_path)
