"""Association statistics for categorical variables."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations

import pandas as pd
from scipy.stats import chi2_contingency

RESULT_COLUMNS = [
    "variable_1",
    "variable_2",
    "n",
    "chi2",
    "dof",
    "p_value",
    "cramers_v",
    "min_expected",
    "low_expected_ratio",
    "chi_square_reliable",
]


def prepare_categorical_data(
    frame: pd.DataFrame,
    columns: Sequence[str],
    missing_label: str = "未知",
) -> pd.DataFrame:
    """Copy selected categorical columns and label their missing values."""

    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing categorical columns: {', '.join(missing)}")
    result = frame.loc[:, list(columns)].copy()
    return result.fillna(missing_label).astype("string")


def cramers_v_bias_corrected(contingency: pd.DataFrame) -> float:
    """Calculate Bergsma/Wicher bias-corrected Cramér's V."""

    observed = contingency.to_numpy()
    n = int(observed.sum())
    if n <= 1 or min(observed.shape) <= 1:
        return 0.0

    chi2 = float(chi2_contingency(observed, correction=False)[0])
    rows, columns = observed.shape
    phi2 = chi2 / n
    phi2_corrected = max(0.0, phi2 - ((columns - 1) * (rows - 1)) / (n - 1))
    rows_corrected = rows - ((rows - 1) ** 2) / (n - 1)
    columns_corrected = columns - ((columns - 1) ** 2) / (n - 1)
    denominator = min(rows_corrected - 1, columns_corrected - 1)
    return 0.0 if denominator <= 0 else float((phi2_corrected / denominator) ** 0.5)


def pairwise_categorical_associations(
    frame: pd.DataFrame,
    columns: Sequence[str],
) -> pd.DataFrame:
    """Calculate association statistics for every unordered column pair."""

    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing categorical columns: {', '.join(missing)}")

    records: list[dict[str, object]] = []
    for variable_1, variable_2 in combinations(columns, 2):
        contingency = pd.crosstab(frame[variable_1], frame[variable_2], dropna=False)
        observed = contingency.to_numpy()
        n = int(observed.sum())

        if n == 0 or min(observed.shape) <= 1:
            chi2 = 0.0
            dof = 0
            p_value = 1.0
            expected = observed.astype(float)
            cramers_v = 0.0
        else:
            chi2, p_value, dof, expected = chi2_contingency(observed, correction=False)
            chi2 = float(chi2)
            p_value = float(p_value)
            dof = int(dof)
            cramers_v = cramers_v_bias_corrected(contingency)

        min_expected = float(expected.min()) if expected.size else 0.0
        low_expected_ratio = float((expected < 5).mean()) if expected.size else 1.0
        reliable = bool(dof > 0 and min_expected >= 1 and low_expected_ratio <= 0.2)
        records.append(
            {
                "variable_1": variable_1,
                "variable_2": variable_2,
                "n": n,
                "chi2": chi2,
                "dof": dof,
                "p_value": p_value,
                "cramers_v": cramers_v,
                "min_expected": min_expected,
                "low_expected_ratio": low_expected_ratio,
                "chi_square_reliable": reliable,
            }
        )

    return pd.DataFrame.from_records(records, columns=RESULT_COLUMNS)


def association_matrix(
    results: pd.DataFrame,
    columns: Sequence[str],
    value_column: str,
) -> pd.DataFrame:
    """Convert pairwise long-form results into a symmetric square matrix."""

    if value_column not in results.columns:
        raise ValueError(f"Result column does not exist: {value_column}")

    is_boolean = value_column == "chi_square_reliable"
    matrix = pd.DataFrame(index=columns, columns=columns, dtype=bool if is_boolean else float)
    diagonal: bool | float
    if is_boolean:
        diagonal = True
    elif value_column == "p_value":
        diagonal = 0.0
    else:
        diagonal = 1.0

    for column in columns:
        matrix.loc[column, column] = diagonal
    for row in results.itertuples(index=False):
        variable_1 = row.variable_1
        variable_2 = row.variable_2
        value = getattr(row, value_column)
        matrix.loc[variable_1, variable_2] = value
        matrix.loc[variable_2, variable_1] = value
    return matrix
