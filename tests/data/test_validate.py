import pandas as pd

from cumcm2022c.data.validate import validate_composition_sums, validate_table_structure


def test_validate_composition_sum_includes_boundaries_without_mutating_input() -> None:
    frame = pd.DataFrame({"SiO2": [85.0, 105.0, 84.99, 105.01], "PbO": [None] * 4})

    result = validate_composition_sums(frame, ["SiO2", "PbO"])

    assert result["composition_sum"].tolist() == [85.0, 105.0, 84.99, 105.01]
    assert result["is_valid_composition"].tolist() == [True, True, False, False]
    assert frame["PbO"].isna().all()
    assert "composition_sum" not in frame.columns


def test_validate_table_structure_reports_actionable_issue_codes() -> None:
    frame = pd.DataFrame(
        [[None, "bad", 1.0]],
        columns=["采样点", "SiO2", "SiO2"],
    )

    issues = validate_table_structure(frame, ["采样点"], ["SiO2"])

    assert {issue.code for issue in issues} == {
        "duplicate_column",
        "missing_identifier",
        "non_numeric_component",
    }
