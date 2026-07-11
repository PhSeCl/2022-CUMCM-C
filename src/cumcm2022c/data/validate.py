"""Non-destructive structural and composition validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd
import pandera.pandas as pa


@dataclass(frozen=True)
class ValidationIssue:
    """One actionable table validation problem."""

    code: str
    column: str | None
    message: str


def validate_composition_sums(
    frame: pd.DataFrame,
    component_columns: Sequence[str],
    lower: float = 85.0,
    upper: float = 105.0,
) -> pd.DataFrame:
    """Return a copy annotated with component totals and validity flags."""

    missing = [column for column in component_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing component columns: {', '.join(missing)}")

    result = frame.copy()
    numeric = result.loc[:, list(component_columns)].apply(pd.to_numeric, errors="raise")
    result["composition_sum"] = numeric.sum(axis=1, skipna=True)
    result["is_valid_composition"] = result["composition_sum"].between(
        lower, upper, inclusive="both"
    )
    return result


def validate_table_structure(
    frame: pd.DataFrame,
    identifier_columns: Sequence[str],
    component_columns: Sequence[str],
) -> list[ValidationIssue]:
    """Collect structural issues without changing or filtering the table."""

    issues: list[ValidationIssue] = []
    duplicated = frame.columns[frame.columns.duplicated()].unique().tolist()
    issues.extend(
        ValidationIssue("duplicate_column", str(column), f"Duplicate column: {column}")
        for column in duplicated
    )

    for column in identifier_columns:
        if column not in frame.columns:
            issues.append(
                ValidationIssue("missing_column", column, f"Missing identifier column: {column}")
            )
            continue
        values = frame.loc[:, column]
        if isinstance(values, pd.DataFrame):
            values = values.iloc[:, 0]
        missing_identifier = values.isna() | values.astype("string").str.strip().eq("")
        if missing_identifier.any():
            issues.append(
                ValidationIssue(
                    "missing_identifier", column, f"Missing values in identifier column: {column}"
                )
            )

    unique_frame = frame.loc[:, ~frame.columns.duplicated()].copy()
    available_components = [
        column for column in component_columns if column in unique_frame.columns
    ]
    for column in component_columns:
        if column not in unique_frame.columns:
            issues.append(
                ValidationIssue("missing_column", column, f"Missing component column: {column}")
            )

    if available_components:
        schema = pa.DataFrameSchema(
            {
                column: pa.Column(float, nullable=True, coerce=True)
                for column in available_components
            },
            strict=False,
            coerce=True,
        )
        try:
            schema.validate(unique_frame, lazy=True)
        except pa.errors.SchemaErrors as error:
            invalid_columns = set(error.failure_cases["column"].dropna().astype(str))
            issues.extend(
                ValidationIssue(
                    "non_numeric_component",
                    column,
                    f"Component column contains non-numeric values: {column}",
                )
                for column in available_components
                if column in invalid_columns
            )

    return issues
